"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


@pytest.fixture
def client():
    """Create test client for FastAPI app with rate limiting disabled."""
    # Patch config to disable rate limiting before importing app
    with patch('main.config') as mock_config:
        # Create a mock that returns appropriate values
        def config_get(key, default=None):
            if key == "security.rate_limit":
                return {"enabled": False}
            if key == "security.headers":
                return {"enabled": True}
            if key == "security.auth":
                return {"enabled": False}
            return default
        
        mock_config.get = config_get
        mock_config.metrics_enabled = False
        mock_config.copilot_log_dir = "./logs/copilot"
        mock_config.repository_name = "test-repo"
        
        # Need to reload the app with patched config
        # Instead, we'll just clear the rate limit tracking
        from main import app
        
        # Find and reset the rate limit middleware if it exists
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and 'RateLimit' in str(middleware.cls):
                # Middleware is already added, we need a different approach
                pass
        
        # Patch the rate limit middleware dispatch to pass through
        with patch('src.api.middleware.rate_limit.RateLimitMiddleware.dispatch') as mock_dispatch:
            async def passthrough(request, call_next):
                return await call_next(request)
            mock_dispatch.side_effect = passthrough
            yield TestClient(app)


@pytest.fixture
def mock_git_ops():
    """Mock GitOperations class for testing."""
    with patch('main.GitOperations') as MockClass:
        mock_instance = Mock()
        MockClass.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_copilot_cli():
    """Mock copilot_cli for testing."""
    with patch('main.copilot_cli') as mock:
        yield mock


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test GET / returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "0.1.0"
    
    def test_get_repo(self, client, mock_git_ops):
        """Test GET /repo returns repository information."""
        mock_git_ops.get_repository_name.return_value = "test-repo"
        
        with patch('main.config') as mock_config:
            mock_config.repository_name = "configured-repo"
            
            response = client.get("/repo")
            
            assert response.status_code == 200
            data = response.json()
            assert data["repository"] == "test-repo"
            assert data["configured_name"] == "configured-repo"
    
    def test_get_repo_error(self, client, mock_git_ops):
        """Test GET /repo with git error."""
        mock_git_ops.get_repository_name.side_effect = Exception("Git error")
        
        response = client.get("/repo")
        
        assert response.status_code == 500
        assert "detail" in response.json()
    
    def test_get_current_branch(self, client, mock_git_ops):
        """Test GET /branch/current returns current branch."""
        mock_git_ops.get_current_branch.return_value = "main"
        
        response = client.get("/branch/current")
        
        assert response.status_code == 200
        data = response.json()
        assert data["branch"] == "main"
    
    def test_get_current_branch_error(self, client, mock_git_ops):
        """Test GET /branch/current with git error."""
        mock_git_ops.get_current_branch.side_effect = RuntimeError("Not a git repo")
        
        response = client.get("/branch/current")
        
        assert response.status_code == 500
    
    def test_select_branch_success(self, client, mock_git_ops):
        """Test POST /branch/select successfully switches branch."""
        mock_git_ops.switch_branch.return_value = {
            "status": "success",
            "branch": "develop",
            "message": "Switched to branch 'develop'"
        }
        
        response = client.post(
            "/branch/select",
            json={"branch": "develop"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["branch"] == "develop"
    
    def test_select_branch_invalid(self, client, mock_git_ops):
        """Test POST /branch/select with invalid branch."""
        mock_git_ops.switch_branch.side_effect = RuntimeError("Branch not found")
        
        response = client.post(
            "/branch/select",
            json={"branch": "invalid"}
        )
        
        assert response.status_code == 400
        assert "detail" in response.json()
    
    def test_select_branch_missing_parameter(self, client):
        """Test POST /branch/select without branch parameter."""
        response = client.post("/branch/select", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_list_worktrees(self, client, mock_git_ops):
        """Test GET /worktrees returns worktree list."""
        mock_git_ops.list_worktrees.return_value = [
            {
                "path": "/repo/main",
                "branch": "main",
                "HEAD": "abc123"
            },
            {
                "path": "/repo/worktrees/feature",
                "branch": "feature/test",
                "HEAD": "def456"
            }
        ]
        
        response = client.get("/worktrees")
        
        assert response.status_code == 200
        data = response.json()
        assert "worktrees" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["worktrees"]) == 2
    
    def test_list_worktrees_error(self, client, mock_git_ops):
        """Test GET /worktrees with git error."""
        mock_git_ops.list_worktrees.side_effect = RuntimeError("Git error")
        
        response = client.get("/worktrees")
        
        assert response.status_code == 500
    
    def test_create_worktree_success(self, client, mock_git_ops):
        """Test POST /worktree/create successfully creates worktree."""
        mock_git_ops.create_worktree.return_value = {
            "status": "success",
            "path": "./worktrees/test",
            "branch": "test-branch",
            "message": "Worktree created"
        }
        
        response = client.post(
            "/worktree/create",
            json={
                "path": "./worktrees/test",
                "branch": "test-branch",
                "create_branch": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["path"] == "./worktrees/test"
    
    def test_create_worktree_with_new_branch(self, client, mock_git_ops):
        """Test POST /worktree/create with create_branch flag."""
        mock_git_ops.create_worktree.return_value = {
            "status": "success",
            "path": "./worktrees/new",
            "branch": "new-branch",
            "message": "Worktree created"
        }
        
        response = client.post(
            "/worktree/create",
            json={
                "path": "./worktrees/new",
                "branch": "new-branch",
                "create_branch": True
            }
        )
        
        assert response.status_code == 200
        mock_git_ops.create_worktree.assert_called_with(
            path="./worktrees/new",
            branch="new-branch",
            create_branch=True
        )
    
    def test_create_worktree_error(self, client, mock_git_ops):
        """Test POST /worktree/create with error."""
        mock_git_ops.create_worktree.side_effect = RuntimeError("Path exists")
        
        response = client.post(
            "/worktree/create",
            json={
                "path": "./worktrees/test",
                "branch": "test"
            }
        )
        
        assert response.status_code == 400
    
    def test_create_worktree_missing_parameters(self, client):
        """Test POST /worktree/create without required parameters."""
        response = client.post("/worktree/create", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_execute_prompt_success(self, client, mock_copilot_cli):
        """Test POST /prompt executes copilot prompt successfully."""
        mock_copilot_cli.execute_prompt.return_value = {
            "status": "success",
            "output": {"response": "test answer"},
            "prompt": "test question"
        }
        
        response = client.post(
            "/prompt",
            json={"prompt": "test question"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "output" in data
    
    def test_execute_prompt_with_options(self, client, mock_copilot_cli):
        """Test POST /prompt with branch, worktree, and session_id options."""
        mock_copilot_cli.execute_prompt.return_value = {
            "status": "success",
            "output": "response",
            "prompt": "test"
        }
        
        response = client.post(
            "/prompt",
            json={
                "prompt": "test",
                "options": {
                    "branch": "main",
                    "worktree": "./worktrees/test",
                    "session_id": "abc123"
                }
            }
        )
        
        assert response.status_code == 200
        # Verify options were passed
        mock_copilot_cli.execute_prompt.assert_called_once()
        call_args = mock_copilot_cli.execute_prompt.call_args
        assert call_args[1]['options']['session_id'] == 'abc123'
    
    def test_execute_prompt_cli_not_available(self, client, mock_copilot_cli):
        """Test POST /prompt when CLI is not available."""
        mock_copilot_cli.execute_prompt.return_value = {
            "status": "error",
            "message": "Copilot CLI is not installed"
        }
        
        response = client.post(
            "/prompt",
            json={"prompt": "test"}
        )
        
        assert response.status_code == 400
        assert "detail" in response.json()
    
    def test_execute_prompt_missing_parameter(self, client):
        """Test POST /prompt without prompt parameter."""
        response = client.post("/prompt", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_execute_prompt_async_success(self, client, mock_copilot_cli):
        """Test POST /prompt/async executes async prompt successfully."""
        # Mock the async function to return a coroutine
        async def mock_async_execute(*args, **kwargs):
            return {
                "status": "success",
                "output": {"response": "async answer"},
                "prompt": "async question"
            }
        
        mock_copilot_cli.execute_prompt_async = mock_async_execute
        
        response = client.post(
            "/prompt/async",
            json={"prompt": "async question"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_execute_prompt_async_error(self, client, mock_copilot_cli):
        """Test POST /prompt/async with error."""
        # Mock the async function to return a coroutine
        async def mock_async_execute(*args, **kwargs):
            return {
                "status": "error",
                "message": "Timeout"
            }
        
        mock_copilot_cli.execute_prompt_async = mock_async_execute
        
        response = client.post(
            "/prompt/async",
            json={"prompt": "test"}
        )
        
        assert response.status_code == 400
    
    def test_web_interface(self, client):
        """Test GET /ui returns HTML page or 404 fallback."""
        response = client.get("/ui")
        
        # The endpoint should return either:
        # - 200 with React app if built (FileResponse)
        # - 404 with fallback message if not built (HTMLResponse)
        assert response.status_code in [200, 404]
        assert "text/html" in response.headers["content-type"]
        
        if response.status_code == 404:
            # UI not built - verify fallback message
            assert b"React UI Not Built" in response.content
            assert b"legacy HTML interface" in response.content
        else:
            # React UI is built - would serve index.html
            pass
    
    @pytest.mark.skip(reason="Legacy UI endpoint not yet implemented - see DUAL_UI_SETUP.md")
    def test_legacy_ui(self, client):
        """Test GET /legacy-ui returns legacy HTML interface."""
        response = client.get("/legacy-ui")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Agent CLI Orchestrator" in response.content
        assert b"Repository Information" in response.content
        assert b"Copilot CLI Prompt" in response.content
    
    def test_api_docs_available(self, client):
        """Test that OpenAPI docs are available."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Agent CLI Orchestrator"    

    def test_logs_endpoint_available(self, client):
        """Test GET /logs returns activity entries."""
        response = client.get("/logs")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "count" in data

    def test_list_branches_success(self, client, mock_git_ops):
        """Test GET /branches returns list of branches."""
        mock_git_ops.list_branches.return_value = [
            {"name": "main", "current": True, "type": "local"},
            {"name": "feature/test", "current": False, "type": "local"},
            {"name": "origin/main", "current": False, "type": "remote"}
        ]
        
        response = client.get("/branches")
        
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "count" in data
        assert data["count"]["total"] == 3
        assert data["count"]["local"] == 2
        assert data["count"]["remote"] == 1
        assert len(data["branches"]) == 3
    
    def test_list_branches_error(self, client, mock_git_ops):
        """Test GET /branches handles errors."""
        mock_git_ops.list_branches.side_effect = RuntimeError("Git error")
        
        response = client.get("/branches")
        
        assert response.status_code == 500
        assert "detail" in response.json()
    
    def test_list_sessions_success(self, client, mock_copilot_cli):
        """Test GET /copilot/sessions returns list of sessions."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "success",
            "sessions": [
                {"session_id": "abc123", "status": "active"},
                {"session_id": "def456", "status": "active"}
            ],
            "count": 2
        }
        
        response = client.get("/copilot/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["sessions"]) == 2
    
    def test_list_sessions_empty(self, client, mock_copilot_cli):
        """Test GET /copilot/sessions with no active sessions."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "success",
            "sessions": [],
            "count": 0
        }
        
        response = client.get("/copilot/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["sessions"] == []
    
    def test_list_sessions_error(self, client, mock_copilot_cli):
        """Test GET /copilot/sessions handles errors."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "error",
            "message": "Copilot CLI not available"
        }
        
        response = client.get("/copilot/sessions")
        
        assert response.status_code == 400
        assert "detail" in response.json()
