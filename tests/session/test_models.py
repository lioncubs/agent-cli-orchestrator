"""Tests for session models."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.session.models import (
    SessionType,
    SessionStatus,
    Turn,
    Session,
    GitIdentity
)


class TestSessionType:
    """Test SessionType enum."""
    
    def test_session_types(self):
        """Test all session type values."""
        assert SessionType.QUERY == "query"
        assert SessionType.RESEARCH == "research"
        assert SessionType.DELEGATION == "delegation"
    
    def test_session_type_is_string(self):
        """Test that SessionType values are strings."""
        assert isinstance(SessionType.QUERY.value, str)
        assert isinstance(SessionType.RESEARCH.value, str)
        assert isinstance(SessionType.DELEGATION.value, str)


class TestSessionStatus:
    """Test SessionStatus enum."""
    
    def test_session_statuses(self):
        """Test all session status values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.COMMITTED == "committed"
        assert SessionStatus.PR_CREATED == "pr_created"
        assert SessionStatus.MERGED == "merged"
        assert SessionStatus.ABANDONED == "abandoned"
        assert SessionStatus.CLOSED == "closed"
    
    def test_session_status_is_string(self):
        """Test that SessionStatus values are strings."""
        for status in SessionStatus:
            assert isinstance(status.value, str)


class TestGitIdentity:
    """Test GitIdentity model."""
    
    def test_create_git_identity(self):
        """Test creating a GitIdentity."""
        identity = GitIdentity(name="John Doe", email="john@example.com")
        assert identity.name == "John Doe"
        assert identity.email == "john@example.com"
    
    def test_git_identity_validation(self):
        """Test GitIdentity field validation."""
        # Should require both name and email
        with pytest.raises(Exception):
            GitIdentity(name="John Doe")
        
        with pytest.raises(Exception):
            GitIdentity(email="john@example.com")


class TestTurn:
    """Test Turn model."""
    
    def test_create_turn(self):
        """Test creating a Turn."""
        now = datetime.utcnow()
        turn = Turn(
            id=1,
            prompt="Test prompt",
            response="Test response",
            response_summary="Summary",
            timestamp=now
        )
        assert turn.id == 1
        assert turn.prompt == "Test prompt"
        assert turn.response == "Test response"
        assert turn.response_summary == "Summary"
        assert turn.files_analyzed == []
        assert turn.files_changed == []
        assert turn.timestamp == now
    
    def test_turn_with_files(self):
        """Test Turn with file lists."""
        now = datetime.utcnow()
        turn = Turn(
            id=1,
            prompt="Test",
            response="Response",
            response_summary="Summary",
            files_analyzed=["file1.py", "file2.py"],
            files_changed=["file1.py"],
            timestamp=now
        )
        assert turn.files_analyzed == ["file1.py", "file2.py"]
        assert turn.files_changed == ["file1.py"]
    
    def test_turn_serialization(self):
        """Test Turn can be serialized to dict."""
        now = datetime.utcnow()
        turn = Turn(
            id=1,
            prompt="Test",
            response="Response",
            response_summary="Summary",
            timestamp=now
        )
        data = turn.model_dump()
        assert data["id"] == 1
        assert data["prompt"] == "Test"
        assert isinstance(data, dict)


class TestSession:
    """Test Session model."""
    
    def test_create_minimal_session(self):
        """Test creating a session with minimal fields."""
        now = datetime.utcnow()
        session_id = uuid4()
        
        session = Session(
            id=session_id,
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
        
        assert session.id == session_id
        assert session.type == SessionType.QUERY
        assert session.status == SessionStatus.ACTIVE
        assert session.repo_name == "test-repo"
        assert session.user_id == "user123"
        assert session.created_at == now
        assert session.last_activity_at == now
        assert session.turns == []
        assert session.files_changed == []
        assert session.is_temporary is False
    
    def test_create_full_session(self):
        """Test creating a session with all fields."""
        now = datetime.utcnow()
        session_id = uuid4()
        identity = GitIdentity(name="John Doe", email="john@example.com")
        
        turn = Turn(
            id=1,
            prompt="Test",
            response="Response",
            response_summary="Summary",
            timestamp=now
        )
        
        session = Session(
            id=session_id,
            type=SessionType.DELEGATION,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            user_identity=identity,
            created_at=now,
            last_activity_at=now,
            expires_at=now,
            copilot_session_id="copilot-123",
            base_branch="main",
            base_commit="abc123",
            session_branch="feature/test",
            worktree_path="/path/to/worktree",
            is_temporary=True,
            turns=[turn],
            commit_sha="def456",
            files_changed=["file1.py"],
            pr_url="https://github.com/user/repo/pull/1"
        )
        
        assert session.user_identity == identity
        assert session.copilot_session_id == "copilot-123"
        assert session.base_branch == "main"
        assert session.base_commit == "abc123"
        assert session.session_branch == "feature/test"
        assert session.worktree_path == "/path/to/worktree"
        assert session.is_temporary is True
        assert len(session.turns) == 1
        assert session.commit_sha == "def456"
        assert session.files_changed == ["file1.py"]
        assert session.pr_url == "https://github.com/user/repo/pull/1"
    
    def test_session_serialization(self):
        """Test Session can be serialized to dict."""
        now = datetime.utcnow()
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            created_at=now,
            last_activity_at=now
        )
        
        data = session.model_dump()
        assert isinstance(data, dict)
        assert data["type"] == "query"
        assert data["status"] == "active"
        assert data["repo_name"] == "test-repo"
    
    def test_session_with_git_identity(self):
        """Test session with git identity."""
        now = datetime.utcnow()
        identity = GitIdentity(name="Test User", email="test@example.com")
        
        session = Session(
            id=uuid4(),
            type=SessionType.DELEGATION,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="user123",
            user_identity=identity,
            created_at=now,
            last_activity_at=now
        )
        
        assert session.user_identity.name == "Test User"
        assert session.user_identity.email == "test@example.com"
