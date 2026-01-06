"""Tests for session API routes."""

import pytest
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient

from src.session.models import SessionType, SessionStatus, GitIdentity
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.api.routes.sessions import router, init_session_routes


@pytest.fixture
def session_store():
    """Create a fresh session store."""
    return SessionStore(default_ttl_hours=24)


@pytest.fixture
def session_manager(session_store):
    """Create a session manager."""
    return SessionManager(store=session_store)


@pytest.fixture
def client(session_store, session_manager):
    """Create a test client with session routes."""
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    # Initialize routes with dependencies
    init_session_routes(session_store, session_manager)
    
    return TestClient(app)


class TestCreateSession:
    """Test POST /sessions endpoint."""
    
    def test_create_query_session(self, client):
        """Test creating a query session."""
        response = client.post("/sessions", json={
            "type": "query",
            "repo_name": "test-repo",
            "user_id": "user123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Session %s created successfully" % data["session"]["id"]
        assert data["session"]["type"] == "query"
        assert data["session"]["status"] == "active"
        assert data["session"]["repo_name"] == "test-repo"
        assert data["session"]["user_id"] == "user123"
    
    def test_create_delegation_session(self, client):
        """Test creating a delegation session with full details."""
        response = client.post("/sessions", json={
            "type": "delegation",
            "repo_name": "test-repo",
            "user_id": "user123",
            "user_identity": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "base_branch": "main",
            "is_temporary": True,
            "ttl_hours": 12
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["session"]["type"] == "delegation"
        assert data["session"]["user_identity"]["name"] == "John Doe"
        assert data["session"]["base_branch"] == "main"
        assert data["session"]["is_temporary"] is True
    
    def test_create_session_invalid_type(self, client):
        """Test creating session with invalid type."""
        response = client.post("/sessions", json={
            "type": "invalid",
            "repo_name": "test-repo",
            "user_id": "user123"
        })
        
        assert response.status_code == 422  # Validation error


class TestListSessions:
    """Test GET /sessions endpoint."""
    
    def test_list_empty_sessions(self, client):
        """Test listing when no sessions exist."""
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []
        assert data["total"] == 0
        assert data["offset"] == 0
    
    def test_list_all_sessions(self, client, session_manager):
        """Test listing all sessions."""
        # Create some sessions
        for i in range(3):
            session_manager.create_session(
                session_type=SessionType.QUERY,
                repo_name="test-repo",
                user_id=f"user{i}"
            )
        
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 3
        assert data["total"] == 3
    
    def test_list_sessions_filter_by_user(self, client, session_manager):
        """Test filtering sessions by user ID."""
        session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user1"
        )
        session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user2"
        )
        
        response = client.get("/sessions?user_id=user1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["user_id"] == "user1"
    
    def test_list_sessions_filter_by_type(self, client, session_manager):
        """Test filtering sessions by type."""
        session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user1"
        )
        session_manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user1"
        )
        
        response = client.get("/sessions?session_type=query")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["type"] == "query"
    
    def test_list_sessions_pagination(self, client, session_manager):
        """Test pagination of session list."""
        # Create 10 sessions
        for i in range(10):
            session_manager.create_session(
                session_type=SessionType.QUERY,
                repo_name="test-repo",
                user_id="user1"
            )
        
        # Get first page
        response = client.get("/sessions?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 5
        assert data["total"] == 10
        
        # Get second page
        response = client.get("/sessions?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 5


class TestGetSession:
    """Test GET /sessions/{id} endpoint."""
    
    def test_get_existing_session(self, client, session_manager):
        """Test getting an existing session."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.get(f"/sessions/{session.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["id"] == str(session.id)
        assert data["session"]["user_id"] == "user123"
    
    def test_get_nonexistent_session(self, client):
        """Test getting a non-existent session."""
        fake_id = uuid4()
        response = client.get(f"/sessions/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestContinueSession:
    """Test POST /sessions/{id}/continue endpoint."""
    
    def test_continue_session(self, client, session_manager):
        """Test continuing a session."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.post(f"/sessions/{session.id}/continue", json={
            "prompt": "What is the weather?",
            "response_summary": "Weather is sunny",
            "files_analyzed": ["weather.py"],
            "files_changed": []
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["session"]["turns"]) == 1
        assert data["session"]["turns"][0]["prompt"] == "What is the weather?"
    
    def test_continue_session_without_summary(self, client, session_manager):
        """Test continuing session without response summary."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.post(f"/sessions/{session.id}/continue", json={
            "prompt": "Long prompt that will be truncated as summary"
        })
        
        assert response.status_code == 200
    
    def test_continue_nonexistent_session(self, client):
        """Test continuing a non-existent session."""
        fake_id = uuid4()
        response = client.post(f"/sessions/{fake_id}/continue", json={
            "prompt": "Test"
        })
        
        assert response.status_code == 404
    
    def test_continue_inactive_session(self, client, session_manager):
        """Test continuing an inactive session."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        # Mark as completed
        session_manager.complete_session(session.id)
        
        response = client.post(f"/sessions/{session.id}/continue", json={
            "prompt": "Test"
        })
        
        assert response.status_code == 404


class TestDeleteSession:
    """Test DELETE /sessions/{id} endpoint."""
    
    def test_delete_session_permanently(self, client, session_manager):
        """Test permanently deleting a session."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.delete(f"/sessions/{session.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]
        
        # Verify it's gone
        assert session_manager.get_session(session.id) is None
    
    def test_abandon_session(self, client, session_manager):
        """Test abandoning a session."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.delete(f"/sessions/{session.id}?abandon=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "abandoned" in data["message"]
        
        # Verify it's marked as abandoned
        retrieved = session_manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.ABANDONED
    
    def test_delete_nonexistent_session(self, client):
        """Test deleting a non-existent session."""
        fake_id = uuid4()
        response = client.delete(f"/sessions/{fake_id}")
        
        assert response.status_code == 404


class TestCompleteSession:
    """Test POST /sessions/{id}/complete endpoint."""
    
    def test_complete_session_basic(self, client, session_manager):
        """Test completing a session without commit/PR."""
        session = session_manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.post(f"/sessions/{session.id}/complete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "completed"
    
    def test_complete_session_with_commit(self, client, session_manager):
        """Test completing a session with commit SHA."""
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123"
        )
        
        response = client.post(
            f"/sessions/{session.id}/complete?commit_sha=abc123"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "committed"
        assert data["session"]["commit_sha"] == "abc123"
    
    def test_complete_session_with_pr(self, client, session_manager):
        """Test completing a session with PR URL."""
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123"
        )
        
        pr_url = "https://github.com/user/repo/pull/123"
        response = client.post(
            f"/sessions/{session.id}/complete?pr_url={pr_url}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "pr_created"
        assert data["session"]["pr_url"] == pr_url
    
    def test_complete_nonexistent_session(self, client):
        """Test completing a non-existent session."""
        fake_id = uuid4()
        response = client.post(f"/sessions/{fake_id}/complete")
        
        assert response.status_code == 404
