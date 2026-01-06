"""Tests for query and research API routes."""

import pytest
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.session.models import SessionType, SessionStatus, ResearchArtifact
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.query.service import QueryService
from src.query.research_service import ResearchService
from src.registry.research_store import ResearchStore
from src.permissions.tool_policy import ToolPolicy
from src.api.routes.query import router, init_query_routes


@pytest.fixture
def session_store():
    """Create a fresh session store."""
    return SessionStore(default_ttl_hours=24)


@pytest.fixture
def session_manager(session_store):
    """Create a session manager."""
    return SessionManager(store=session_store)


@pytest.fixture
def research_store():
    """Create a fresh research store."""
    return ResearchStore()


@pytest.fixture
def query_service():
    """Create a query service."""
    return QueryService()


@pytest.fixture
def research_service(research_store, query_service):
    """Create a research service."""
    return ResearchService(research_store, query_service)


@pytest.fixture
def tool_policy():
    """Create a tool policy."""
    return ToolPolicy()


@pytest.fixture
def client(session_store, session_manager, research_store, query_service, research_service, tool_policy):
    """Create a test client with query routes."""
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    # Initialize routes with dependencies
    init_query_routes(
        query_service,
        research_service,
        session_manager,
        research_store,
        tool_policy
    )
    
    return TestClient(app)


class TestExecuteQuery:
    """Test POST /query endpoint."""
    
    @patch.object(QueryService, 'read_file')
    def test_read_file_query(self, mock_read_file, client):
        """Test executing a read_file query."""
        mock_read_file.return_value = {
            "status": "success",
            "file_path": "test.py",
            "content": "def test(): pass",
            "lines": 1,
            "size": 18
        }
        
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "read_file",
            "parameters": {
                "file_path": "test.py"
            },
            "user_id": "user123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
        assert data["result"]["file_path"] == "test.py"
    
    @patch.object(QueryService, 'list_files')
    def test_list_files_query(self, mock_list_files, client):
        """Test executing a list_files query."""
        mock_list_files.return_value = {
            "status": "success",
            "directory": ".",
            "files": [
                {"path": "test.py", "name": "test.py", "size": 100}
            ],
            "directories": [],
            "total_files": 1,
            "total_directories": 0
        }
        
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "list_files",
            "parameters": {
                "directory": "."
            },
            "user_id": "user123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["total_files"] == 1
    
    @patch.object(QueryService, 'search_code')
    def test_search_code_query(self, mock_search_code, client):
        """Test executing a search_code query."""
        mock_search_code.return_value = {
            "status": "success",
            "pattern": "def",
            "matches": [
                {"file": "test.py", "line": 1, "content": "def test():"}
            ],
            "total_matches": 1,
            "truncated": False
        }
        
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "search_code",
            "parameters": {
                "pattern": "def"
            },
            "user_id": "user123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["total_matches"] == 1
    
    @patch.object(QueryService, 'get_branch_info')
    def test_get_branch_query(self, mock_get_branch, client):
        """Test executing a get_branch query."""
        mock_get_branch.return_value = {
            "status": "success",
            "branch": "main",
            "commit": "abc123",
            "commit_message": "Initial commit"
        }
        
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "get_branch",
            "parameters": {},
            "user_id": "user123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["branch"] == "main"
    
    @patch.object(QueryService, 'list_branches')
    def test_list_branches_query(self, mock_list_branches, client):
        """Test executing a list_branches query."""
        mock_list_branches.return_value = {
            "status": "success",
            "branches": [
                {"name": "main", "current": True},
                {"name": "develop", "current": False}
            ],
            "current_branch": "main",
            "total": 2
        }
        
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "list_branches",
            "parameters": {},
            "user_id": "user123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["result"]["total"] == 2
    
    def test_invalid_operation(self, client):
        """Test query with invalid operation."""
        response = client.post("/query", json={
            "repo_name": "test-repo",
            "operation": "invalid_operation",
            "parameters": {},
            "user_id": "user123"
        })
        
        assert response.status_code == 400
        assert "Unknown operation" in response.json()["detail"]


class TestCompleteResearchSession:
    """Test POST /query/sessions/{id}/complete endpoint."""
    
    def test_complete_research_session_success(self, client, session_manager):
        """Test completing a research session."""
        # Create a research session
        session = session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            base_branch="main"
        )
        
        # Complete it
        response = client.post(
            f"/query/sessions/{session.id}/complete",
            json={
                "summary": "Research completed",
                "findings": [
                    {
                        "file": "test.py",
                        "note": "Found an issue"
                    }
                ],
                "recommendations": ["Fix the issue"],
                "suggested_delegation_prompt": "Fix test.py",
                "cleanup_worktree": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "artifact" in data
        assert data["artifact"]["summary"] == "Research completed"
        assert len(data["artifact"]["findings"]) == 1
        assert len(data["artifact"]["recommendations"]) == 1
    
    def test_complete_nonexistent_session(self, client):
        """Test completing a nonexistent session."""
        fake_id = uuid4()
        
        response = client.post(
            f"/query/sessions/{fake_id}/complete",
            json={
                "summary": "Test",
                "findings": [],
                "recommendations": []
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_complete_non_research_session(self, client, session_manager):
        """Test completing a non-research session fails."""
        # Create a query session (not research)
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.post(
            f"/query/sessions/{session.id}/complete",
            json={
                "summary": "Test",
                "findings": [],
                "recommendations": []
            }
        )
        
        assert response.status_code == 400
        assert "not a research session" in response.json()["detail"].lower()


class TestListResearchArtifacts:
    """Test GET /query/research endpoint."""
    
    def test_list_empty_artifacts(self, client):
        """Test listing when no artifacts exist."""
        response = client.get("/query/research")
        
        assert response.status_code == 200
        data = response.json()
        assert data["artifacts"] == []
        assert data["total"] == 0
        assert data["offset"] == 0
    
    def test_list_artifacts(self, client, session_manager, research_service):
        """Test listing research artifacts."""
        # Create some research sessions and artifacts
        for i in range(3):
            session = session_manager.create_session(
                session_type=SessionType.RESEARCH,
                repo_name=f"repo-{i}",
                user_id="user123",
                base_branch="main"
            )
            
            research_service.generate_research_artifact(
                session=session,
                summary=f"Summary {i}",
                findings=[],
                recommendations=[]
            )
        
        response = client.get("/query/research")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 3
        assert data["total"] == 3
    
    def test_list_artifacts_with_repo_filter(self, client, session_manager, research_service):
        """Test listing artifacts filtered by repository."""
        # Create artifacts for different repos
        for repo in ["repo-a", "repo-b", "repo-a"]:
            session = session_manager.create_session(
                session_type=SessionType.RESEARCH,
                repo_name=repo,
                user_id="user123",
                base_branch="main"
            )
            
            research_service.generate_research_artifact(
                session=session,
                summary="Test",
                findings=[],
                recommendations=[]
            )
        
        response = client.get("/query/research?repo_name=repo-a")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 2
        assert all(a["repo_name"] == "repo-a" for a in data["artifacts"])
    
    def test_list_artifacts_with_user_filter(self, client, session_manager, research_service):
        """Test listing artifacts filtered by user."""
        # Create artifacts for different users
        for user in ["user-1", "user-2", "user-1"]:
            session = session_manager.create_session(
                session_type=SessionType.RESEARCH,
                repo_name="test-repo",
                user_id=user,
                base_branch="main"
            )
            
            research_service.generate_research_artifact(
                session=session,
                summary="Test",
                findings=[],
                recommendations=[]
            )
        
        response = client.get("/query/research?user_id=user-1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 2
        assert all(a["user_id"] == "user-1" for a in data["artifacts"])
    
    def test_list_artifacts_with_pagination(self, client, session_manager, research_service):
        """Test listing artifacts with pagination."""
        # Create 10 artifacts
        for i in range(10):
            session = session_manager.create_session(
                session_type=SessionType.RESEARCH,
                repo_name="test-repo",
                user_id="user123",
                base_branch="main"
            )
            
            research_service.generate_research_artifact(
                session=session,
                summary=f"Summary {i}",
                findings=[],
                recommendations=[]
            )
        
        # Get first page
        response = client.get("/query/research?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 5
        assert data["total"] == 10
        
        # Get second page
        response = client.get("/query/research?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["artifacts"]) == 5


class TestGetResearchArtifact:
    """Test GET /query/research/{id} endpoint."""
    
    def test_get_artifact_success(self, client, session_manager, research_service):
        """Test getting a specific artifact."""
        # Create an artifact
        session = session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            base_branch="main"
        )
        
        artifact = research_service.generate_research_artifact(
            session=session,
            summary="Test research",
            findings=[],
            recommendations=["Do something"]
        )
        
        response = client.get(f"/query/research/{artifact.research_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["artifact"]["research_id"] == str(artifact.research_id)
        assert data["artifact"]["summary"] == "Test research"
    
    def test_get_nonexistent_artifact(self, client):
        """Test getting a nonexistent artifact."""
        fake_id = uuid4()
        
        response = client.get(f"/query/research/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDelegateFromResearch:
    """Test POST /query/research/{id}/delegate endpoint."""
    
    def test_delegate_from_research_success(self, client, session_manager, research_service):
        """Test creating a delegation from research artifact."""
        # Create an artifact
        session = session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            base_branch="main"
        )
        
        artifact = research_service.generate_research_artifact(
            session=session,
            summary="Research complete",
            findings=[],
            recommendations=[],
            suggested_delegation_prompt="Fix the issues"
        )
        
        # Delegate from it
        response = client.post(
            f"/query/research/{artifact.research_id}/delegate",
            json={
                "user_id": "user456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "session_id" in data
        assert data["research_id"] == str(artifact.research_id)
    
    def test_delegate_with_custom_prompt(self, client, session_manager, research_service):
        """Test delegating with a custom prompt."""
        session = session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            base_branch="main"
        )
        
        artifact = research_service.generate_research_artifact(
            session=session,
            summary="Research complete",
            findings=[],
            recommendations=[],
            suggested_delegation_prompt="Original prompt"
        )
        
        response = client.post(
            f"/query/research/{artifact.research_id}/delegate",
            json={
                "user_id": "user456",
                "custom_prompt": "Custom delegation task"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_delegate_from_nonexistent_artifact(self, client):
        """Test delegating from nonexistent artifact."""
        fake_id = uuid4()
        
        response = client.post(
            f"/query/research/{fake_id}/delegate",
            json={
                "user_id": "user123"
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDeleteResearchArtifact:
    """Test DELETE /query/research/{id} endpoint."""
    
    def test_delete_artifact_success(self, client, session_manager, research_service):
        """Test deleting a research artifact."""
        # Create an artifact
        session = session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            base_branch="main"
        )
        
        artifact = research_service.generate_research_artifact(
            session=session,
            summary="Test",
            findings=[],
            recommendations=[]
        )
        
        # Delete it
        response = client.delete(f"/query/research/{artifact.research_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
        
        # Verify it's gone
        get_response = client.get(f"/query/research/{artifact.research_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_artifact(self, client):
        """Test deleting a nonexistent artifact."""
        fake_id = uuid4()
        
        response = client.delete(f"/query/research/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
