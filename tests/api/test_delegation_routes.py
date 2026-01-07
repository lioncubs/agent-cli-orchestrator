"""Tests for delegation API routes."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routes.delegation import (
    router,
    init_delegation_routes,
    CreateDelegationRequest,
    ContinueDelegationRequest,
    CommitDelegationRequest,
    CreatePRRequest
)
from src.session.models import Session, SessionType, SessionStatus, GitIdentity
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.delegation.service import DelegationService


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def session_store():
    """Create a session store."""
    return SessionStore(default_ttl_hours=24)


@pytest.fixture
def session_manager(session_store):
    """Create a session manager."""
    return SessionManager(store=session_store)


@pytest.fixture
def delegation_service(session_store, tmp_path):
    """Create a delegation service with mock repo."""
    import subprocess
    
    # Create mock repo
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_dir, check=True)
    (repo_dir / "README.md").write_text("# Test")
    subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(['git', 'branch', 'main'], cwd=repo_dir, check=True, capture_output=True)
    
    return DelegationService(
        session_store=session_store,
        repo_path=str(repo_dir)
    )


@pytest.fixture
def client(app, session_store, session_manager, delegation_service):
    """Create a test client with initialized routes."""
    init_delegation_routes(session_store, session_manager, delegation_service)
    return TestClient(app)


class TestDelegationRoutes:
    """Test delegation API routes."""
    
    def test_create_delegation_session(self, client):
        """Test creating a delegation session."""
        response = client.post(
            "/delegation/sessions",
            json={
                "repo_name": "test-repo",
                "user_id": "testuser",
                "user_identity": {
                    "name": "Test User",
                    "email": "user@example.com"
                },
                "base_branch": "main"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"]
        assert data["session"]["type"] == "delegation"
        assert data["session"]["worktree_path"] is not None
        assert data["session"]["session_branch"] is not None
    
    def test_create_delegation_session_with_slug(self, client):
        """Test creating delegation session with task slug."""
        response = client.post(
            "/delegation/sessions",
            json={
                "repo_name": "test-repo",
                "user_id": "testuser",
                "user_identity": {
                    "name": "Test User",
                    "email": "user@example.com"
                },
                "base_branch": "main",
                "task_slug": "fix-bug-123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "fix-bug-123" in data["session"]["session_branch"]
    
    def test_create_delegation_session_with_ttl(self, client):
        """Test creating delegation session with custom TTL."""
        response = client.post(
            "/delegation/sessions",
            json={
                "repo_name": "test-repo",
                "user_id": "testuser",
                "user_identity": {
                    "name": "Test User",
                    "email": "user@example.com"
                },
                "base_branch": "main",
                "ttl_hours": 12
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["session"]["expires_at"] is not None
    
    def test_continue_delegation(self, client, session_manager, delegation_service):
        """Test continuing a delegation session."""
        # Create a session first
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        # Continue session
        response = client.post(
            f"/delegation/sessions/{session_id}/continue",
            json={
                "prompt": "Test prompt",
                "response": "Test response",
                "files_analyzed": ["file1.py"],
                "files_changed": ["file2.py"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["session"]["turns"]) == 1
        assert data["session"]["turns"][0]["prompt"] == "Test prompt"
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_commit_delegation_no_changes(self, client, session_manager, delegation_service):
        """Test committing when there are no changes."""
        # Create and initialize session
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        # Try to commit with no changes
        response = client.post(
            f"/delegation/sessions/{session_id}/commit",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "No changes" in data["message"]
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_commit_delegation_with_changes(self, client, session_manager, delegation_service):
        """Test committing with changes."""
        from pathlib import Path
        
        # Create and initialize session
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        # Make changes
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        # Commit changes
        response = client.post(
            f"/delegation/sessions/{session_id}/commit",
            json={"message": "Test commit"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Changes committed" in data["message"]
        assert data["session"]["commit_sha"] is not None
        assert data["session"]["status"] == "committed"
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_commit_delegation_not_found(self, client):
        """Test committing non-existent session."""
        session_id = uuid4()
        
        response = client.post(
            f"/delegation/sessions/{session_id}/commit",
            json={}
        )
        
        assert response.status_code == 404
    
    @patch('src.delegation.pr_manager.PRManager.create_pull_request')
    @patch('src.delegation.pr_manager.PRManager.push_branch')
    def test_create_pr(
        self,
        mock_push,
        mock_create_pr,
        client,
        session_manager,
        delegation_service
    ):
        """Test creating a pull request."""
        from pathlib import Path
        
        # Create, initialize, and commit changes
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        
        # Make and commit changes
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        session = delegation_service.commit_changes(session)
        session_id = session.id
        
        # Mock PR creation - returns a dict now
        from unittest.mock import AsyncMock
        async def async_pr_create(*args, **kwargs):
            return {
                "status": "success",
                "pr_url": "https://github.com/test/repo/pull/123",
                "pr_id": "123",
                "pr_number": 123,
                "message": "PR created successfully",
                "platform": "GitHub"
            }
        mock_create_pr.side_effect = async_pr_create
        
        # Create PR
        response = client.post(
            f"/delegation/sessions/{session_id}/pr",
            json={
                "title": "Test PR",
                "body": "Test description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Pull request created" in data["message"]
        assert data["session"]["pr_url"] == "https://github.com/test/repo/pull/123"
        assert data["session"]["status"] == "pr_created"
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    @patch('src.delegation.pr_manager.PRManager.create_pull_request')
    @patch('src.delegation.pr_manager.PRManager.push_branch')
    def test_create_pr_draft(
        self,
        mock_push,
        mock_create_pr,
        client,
        session_manager,
        delegation_service
    ):
        """Test creating a draft pull request."""
        from pathlib import Path
        
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        session = delegation_service.commit_changes(session)
        session_id = session.id
        
        from unittest.mock import AsyncMock
        async def async_pr_create(*args, **kwargs):
            return {
                "status": "success",
                "pr_url": "https://github.com/test/repo/pull/123",
                "pr_id": "123",
                "pr_number": 123,
                "message": "PR created successfully",
                "platform": "GitHub"
            }
        mock_create_pr.side_effect = async_pr_create
        
        # Create draft PR
        response = client.post(
            f"/delegation/sessions/{session_id}/pr",
            json={
                "title": "Test PR",
                "draft": True
            }
        )
        
        assert response.status_code == 200
        mock_create_pr.assert_called_once()
        assert mock_create_pr.call_args[1]['draft'] is True
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_create_pr_no_commit(self, client, session_manager, delegation_service):
        """Test creating PR without commits."""
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        response = client.post(
            f"/delegation/sessions/{session_id}/pr",
            json={"title": "Test PR"}
        )
        
        assert response.status_code == 400
        assert "no commits" in response.json()["detail"]
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_abandon_delegation(self, client, session_manager, delegation_service):
        """Test abandoning a delegation session."""
        from pathlib import Path
        
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        worktree_path = session.worktree_path
        
        # Abandon
        response = client.delete(f"/delegation/sessions/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "abandoned"
        assert not Path(worktree_path).exists()
    
    def test_abandon_delegation_keep_branch(
        self,
        client,
        session_manager,
        delegation_service
    ):
        """Test abandoning without deleting branch."""
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        # Abandon but keep branch
        response = client.delete(
            f"/delegation/sessions/{session_id}?delete_branch=false"
        )
        
        assert response.status_code == 200
    
    def test_abandon_delegation_not_found(self, client):
        """Test abandoning non-existent session."""
        session_id = uuid4()
        
        response = client.delete(f"/delegation/sessions/{session_id}")
        
        assert response.status_code == 404
    
    def test_get_delegation_status(self, client, session_manager, delegation_service):
        """Test getting delegation status."""
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            base_branch="main"
        )
        session = delegation_service.initialize_delegation(session)
        session_id = session.id
        
        # Get status
        response = client.get(f"/delegation/sessions/{session_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["status"] == "active"
        assert data["base_branch"] == "main"
        assert data["session_branch"] is not None
        assert data["worktree_path"] is not None
        assert data["has_uncommitted_changes"] is False
        
        # Cleanup
        delegation_service.abandon_delegation(session)
    
    def test_get_delegation_status_not_found(self, client):
        """Test getting status of non-existent session."""
        session_id = uuid4()
        
        response = client.get(f"/delegation/sessions/{session_id}/status")
        
        assert response.status_code == 404
