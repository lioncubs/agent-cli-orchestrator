"""Tests for session store."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.session.models import Session, SessionType, SessionStatus
from src.session.store import SessionStore


class TestSessionStore:
    """Test SessionStore functionality."""
    
    @pytest.fixture
    def store(self):
        """Create a fresh session store for each test."""
        return SessionStore(default_ttl_hours=24)
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        now = datetime.utcnow()
        return Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
    
    def test_create_session(self, store, sample_session):
        """Test creating a session."""
        created = store.create(sample_session)
        
        assert created.id == sample_session.id
        assert created.expires_at is not None
        assert created.expires_at > datetime.utcnow()
    
    def test_create_duplicate_session(self, store, sample_session):
        """Test creating a session with duplicate ID fails."""
        store.create(sample_session)
        
        with pytest.raises(ValueError, match="already exists"):
            store.create(sample_session)
    
    def test_get_session(self, store, sample_session):
        """Test retrieving a session."""
        store.create(sample_session)
        retrieved = store.get(sample_session.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_session.id
        assert retrieved.type == sample_session.type
    
    def test_get_nonexistent_session(self, store):
        """Test retrieving a non-existent session."""
        result = store.get(uuid4())
        assert result is None
    
    def test_update_session(self, store, sample_session):
        """Test updating a session."""
        store.create(sample_session)
        
        # Modify the session
        sample_session.status = SessionStatus.COMPLETED
        sample_session.commit_sha = "abc123"
        
        updated = store.update(sample_session)
        
        assert updated.status == SessionStatus.COMPLETED
        assert updated.commit_sha == "abc123"
        
        # Verify it's persisted
        retrieved = store.get(sample_session.id)
        assert retrieved.status == SessionStatus.COMPLETED
        assert retrieved.commit_sha == "abc123"
    
    def test_update_nonexistent_session(self, store, sample_session):
        """Test updating a non-existent session fails."""
        with pytest.raises(ValueError, match="not found"):
            store.update(sample_session)
    
    def test_delete_session(self, store, sample_session):
        """Test deleting a session."""
        store.create(sample_session)
        
        success = store.delete(sample_session.id)
        assert success is True
        
        # Verify it's gone
        result = store.get(sample_session.id)
        assert result is None
    
    def test_delete_nonexistent_session(self, store):
        """Test deleting a non-existent session."""
        success = store.delete(uuid4())
        assert success is False
    
    def test_list_all_sessions(self, store):
        """Test listing all sessions."""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id=f"user{i}",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
            sessions.append(session)
        
        all_sessions = store.list()
        assert len(all_sessions) == 5
    
    def test_list_sessions_by_user(self, store):
        """Test filtering sessions by user ID."""
        # Create sessions for different users
        for i in range(3):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id="user1" if i < 2 else "user2",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        user1_sessions = store.list(user_id="user1")
        assert len(user1_sessions) == 2
        
        user2_sessions = store.list(user_id="user2")
        assert len(user2_sessions) == 1
    
    def test_list_sessions_by_repo(self, store):
        """Test filtering sessions by repository."""
        # Create sessions for different repos
        for i in range(3):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="repo1" if i < 2 else "repo2",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        repo1_sessions = store.list(repo_name="repo1")
        assert len(repo1_sessions) == 2
        
        repo2_sessions = store.list(repo_name="repo2")
        assert len(repo2_sessions) == 1
    
    def test_list_sessions_by_type(self, store):
        """Test filtering sessions by type."""
        # Create sessions of different types
        for session_type in [SessionType.QUERY, SessionType.RESEARCH, SessionType.DELEGATION]:
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=session_type,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        query_sessions = store.list(session_type=SessionType.QUERY)
        assert len(query_sessions) == 1
        assert query_sessions[0].type == SessionType.QUERY
    
    def test_list_sessions_by_status(self, store):
        """Test filtering sessions by status."""
        # Create sessions with different statuses
        for status in [SessionStatus.ACTIVE, SessionStatus.COMPLETED]:
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=status,
                repo_name="test-repo",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        active_sessions = store.list(status=SessionStatus.ACTIVE)
        assert len(active_sessions) == 1
        assert active_sessions[0].status == SessionStatus.ACTIVE
    
    def test_list_sessions_with_pagination(self, store):
        """Test pagination of session list."""
        # Create 10 sessions
        for i in range(10):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        # Get first page
        page1 = store.list(limit=5, offset=0)
        assert len(page1) == 5
        
        # Get second page
        page2 = store.list(limit=5, offset=5)
        assert len(page2) == 5
        
        # Verify no overlap
        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
    
    def test_count_sessions(self, store):
        """Test counting sessions."""
        # Create sessions
        for i in range(5):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        count = store.count()
        assert count == 5
        
        count_by_user = store.count(user_id="user1")
        assert count_by_user == 5
        
        count_by_other = store.count(user_id="user2")
        assert count_by_other == 0
    
    def test_expired_session_handling(self, store):
        """Test that expired sessions are marked as abandoned."""
        now = datetime.utcnow()
        expired_session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user1",
            created_at=now - timedelta(hours=25),
            last_activity_at=now - timedelta(hours=25),
            expires_at=now - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        store.create(expired_session)
        
        # Get the session - should be marked as abandoned
        retrieved = store.get(expired_session.id)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.ABANDONED
    
    def test_clear_store(self, store):
        """Test clearing all sessions."""
        # Create sessions
        for i in range(3):
            now = datetime.utcnow()
            session = Session(
                id=uuid4(),
                type=SessionType.QUERY,
                status=SessionStatus.ACTIVE,
                repo_name="test-repo",
                user_id="user1",
                created_at=now,
                last_activity_at=now
            )
            store.create(session)
        
        store.clear()
        
        all_sessions = store.list()
        assert len(all_sessions) == 0
