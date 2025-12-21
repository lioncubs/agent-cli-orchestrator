"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_git_ops():
    """Mock GitOperations for testing."""
    with patch('main.git_ops') as mock:
        yield mock


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
        """Test GET /ui returns HTML page."""
        response = client.get("/ui")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Agent CLI Orchestrator" in response.content
        assert b"Repository Information" in response.content
    
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
        """Test GET /sessions returns list of sessions."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "success",
            "sessions": [
                {"session_id": "abc123", "status": "active"},
                {"session_id": "def456", "status": "active"}
            ],
            "count": 2
        }
        
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["sessions"]) == 2
    
    def test_list_sessions_empty(self, client, mock_copilot_cli):
        """Test GET /sessions with no active sessions."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "success",
            "sessions": [],
            "count": 0
        }
        
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["sessions"] == []
    
    def test_list_sessions_error(self, client, mock_copilot_cli):
        """Test GET /sessions handles errors."""
        mock_copilot_cli.list_sessions.return_value = {
            "status": "error",
            "message": "Copilot CLI not available"
        }
        
        response = client.get("/sessions")
        
        assert response.status_code == 400
        assert "detail" in response.json()
