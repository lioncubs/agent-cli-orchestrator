"""Tests for session manager."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from src.session.models import (
    Session,
    SessionType,
    SessionStatus,
    GitIdentity
)
from src.session.store import SessionStore
from src.session.manager import SessionManager


class TestSessionManager:
    """Test SessionManager functionality."""
    
    @pytest.fixture
    def store(self):
        """Create a fresh session store."""
        return SessionStore(default_ttl_hours=24)
    
    @pytest.fixture
    def manager(self, store):
        """Create a session manager."""
        return SessionManager(store=store)
    
    def test_create_query_session(self, manager):
        """Test creating a query session."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        assert session.id is not None
        assert isinstance(session.id, UUID)
        assert session.type == SessionType.QUERY
        assert session.status == SessionStatus.ACTIVE
        assert session.repo_name == "test-repo"
        assert session.user_id == "user123"
        assert session.created_at is not None
        assert session.last_activity_at is not None
        assert len(session.turns) == 0
    
    def test_create_session_with_identity(self, manager):
        """Test creating a session with git identity."""
        identity = GitIdentity(name="John Doe", email="john@example.com")
        
        session = manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123",
            user_identity=identity
        )
        
        assert session.user_identity == identity
        assert session.user_identity.name == "John Doe"
        assert session.user_identity.email == "john@example.com"
    
    def test_create_session_with_custom_ttl(self, manager):
        """Test creating a session with custom TTL."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123",
            ttl_hours=12
        )
        
        assert session.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(hours=12)
        # Allow 1 minute tolerance for test execution time
        assert abs((session.expires_at - expected_expiry).total_seconds()) < 60
    
    def test_create_temporary_session(self, manager):
        """Test creating a temporary session."""
        session = manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user123",
            is_temporary=True
        )
        
        assert session.is_temporary is True
    
    def test_get_session(self, manager):
        """Test retrieving a session."""
        created = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        retrieved = manager.get_session(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.type == created.type
    
    def test_get_nonexistent_session(self, manager):
        """Test retrieving a non-existent session."""
        result = manager.get_session(uuid4())
        assert result is None
    
    def test_continue_session(self, manager):
        """Test continuing a session with a new turn."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        updated = manager.continue_session(
            session_id=session.id,
            prompt="What is the weather?",
            response="The weather is sunny.",
            response_summary="Weather is sunny"
        )
        
        assert len(updated.turns) == 1
        assert updated.turns[0].id == 1
        assert updated.turns[0].prompt == "What is the weather?"
        assert updated.turns[0].response == "The weather is sunny."
        assert updated.turns[0].response_summary == "Weather is sunny"
    
    def test_continue_session_multiple_turns(self, manager):
        """Test adding multiple turns to a session."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        # First turn
        manager.continue_session(
            session_id=session.id,
            prompt="First question",
            response="First answer",
            response_summary="Answer 1"
        )
        
        # Second turn
        updated = manager.continue_session(
            session_id=session.id,
            prompt="Second question",
            response="Second answer",
            response_summary="Answer 2"
        )
        
        assert len(updated.turns) == 2
        assert updated.turns[0].id == 1
        assert updated.turns[1].id == 2
        assert updated.turns[1].prompt == "Second question"
    
    def test_continue_session_with_files(self, manager):
        """Test continuing session with file information."""
        session = manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123"
        )
        
        updated = manager.continue_session(
            session_id=session.id,
            prompt="Fix the bug",
            response="Fixed",
            response_summary="Bug fixed",
            files_analyzed=["src/app.py", "tests/test_app.py"],
            files_changed=["src/app.py"]
        )
        
        assert len(updated.turns) == 1
        assert updated.turns[0].files_analyzed == ["src/app.py", "tests/test_app.py"]
        assert updated.turns[0].files_changed == ["src/app.py"]
        assert "src/app.py" in updated.files_changed
    
    def test_continue_session_updates_activity_time(self, manager):
        """Test that continuing a session updates last activity time."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        original_activity_time = session.last_activity_at
        
        # Wait a tiny bit to ensure time difference
        import time
        time.sleep(0.01)
        
        updated = manager.continue_session(
            session_id=session.id,
            prompt="Test",
            response="Response",
            response_summary="Summary"
        )
        
        assert updated.last_activity_at > original_activity_time
    
    def test_continue_nonexistent_session(self, manager):
        """Test continuing a non-existent session fails."""
        with pytest.raises(ValueError, match="not found"):
            manager.continue_session(
                session_id=uuid4(),
                prompt="Test",
                response="Response",
                response_summary="Summary"
            )
    
    def test_continue_inactive_session(self, manager):
        """Test continuing an inactive session fails."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        # Mark as completed
        session.status = SessionStatus.COMPLETED
        manager.store.update(session)
        
        with pytest.raises(ValueError, match="not active"):
            manager.continue_session(
                session_id=session.id,
                prompt="Test",
                response="Response",
                response_summary="Summary"
            )
    
    def test_complete_session(self, manager):
        """Test marking a session as completed."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        completed = manager.complete_session(session.id)
        
        assert completed.status == SessionStatus.COMPLETED
    
    def test_complete_session_with_commit(self, manager):
        """Test completing a session with commit SHA."""
        session = manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123"
        )
        
        completed = manager.complete_session(
            session_id=session.id,
            commit_sha="abc123def456"
        )
        
        assert completed.status == SessionStatus.COMMITTED
        assert completed.commit_sha == "abc123def456"
    
    def test_complete_session_with_pr(self, manager):
        """Test completing a session with PR URL."""
        session = manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name="test-repo",
            user_id="user123"
        )
        
        completed = manager.complete_session(
            session_id=session.id,
            pr_url="https://github.com/user/repo/pull/123"
        )
        
        assert completed.status == SessionStatus.PR_CREATED
        assert completed.pr_url == "https://github.com/user/repo/pull/123"
    
    def test_complete_nonexistent_session(self, manager):
        """Test completing a non-existent session fails."""
        with pytest.raises(ValueError, match="not found"):
            manager.complete_session(uuid4())
    
    def test_abandon_session(self, manager):
        """Test abandoning a session."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        abandoned = manager.abandon_session(session.id)
        
        assert abandoned.status == SessionStatus.ABANDONED
    
    def test_abandon_nonexistent_session(self, manager):
        """Test abandoning a non-existent session fails."""
        with pytest.raises(ValueError, match="not found"):
            manager.abandon_session(uuid4())
    
    def test_close_session(self, manager):
        """Test closing a session."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        closed = manager.close_session(session.id)
        
        assert closed.status == SessionStatus.CLOSED
    
    def test_close_nonexistent_session(self, manager):
        """Test closing a non-existent session fails."""
        with pytest.raises(ValueError, match="not found"):
            manager.close_session(uuid4())
    
    def test_delete_session(self, manager):
        """Test permanently deleting a session."""
        session = manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user123"
        )
        
        success = manager.delete_session(session.id)
        
        assert success is True
        assert manager.get_session(session.id) is None
    
    def test_delete_nonexistent_session(self, manager):
        """Test deleting a non-existent session."""
        success = manager.delete_session(uuid4())
        assert success is False
    
    def test_list_sessions(self, manager):
        """Test listing sessions."""
        # Create multiple sessions
        for i in range(3):
            manager.create_session(
                session_type=SessionType.QUERY,
                repo_name="test-repo",
                user_id=f"user{i}"
            )
        
        sessions = manager.list_sessions()
        assert len(sessions) == 3
    
    def test_list_sessions_with_filters(self, manager):
        """Test listing sessions with filters."""
        # Create sessions for different users
        manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user1"
        )
        manager.create_session(
            session_type=SessionType.RESEARCH,
            repo_name="test-repo",
            user_id="user1"
        )
        manager.create_session(
            session_type=SessionType.QUERY,
            repo_name="test-repo",
            user_id="user2"
        )
        
        # Filter by user
        user1_sessions = manager.list_sessions(user_id="user1")
        assert len(user1_sessions) == 2
        
        # Filter by type
        query_sessions = manager.list_sessions(session_type=SessionType.QUERY)
        assert len(query_sessions) == 2
        
        # Filter by both
        user1_query = manager.list_sessions(
            user_id="user1",
            session_type=SessionType.QUERY
        )
        assert len(user1_query) == 1
