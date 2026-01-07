"""Tests for DelegationService."""

import pytest
import subprocess
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.delegation.service import DelegationService
from src.session.models import Session, SessionType, SessionStatus, GitIdentity
from src.session.store import SessionStore


class TestDelegationService:
    """Test DelegationService functionality."""
    
    @pytest.fixture
    def mock_repo(self, tmp_path):
        """Create a mock git repository."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_dir, check=True)
        
        # Create initial commit
        (repo_dir / "README.md").write_text("# Test Repo")
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(['git', 'branch', 'main'], cwd=repo_dir, check=True, capture_output=True)
        
        return repo_dir
    
    @pytest.fixture
    def session_store(self):
        """Create a session store."""
        return SessionStore(default_ttl_hours=24)
    
    @pytest.fixture
    def agent_identity(self):
        """Create agent identity."""
        return GitIdentity(name="Test Agent", email="agent@example.com")
    
    @pytest.fixture
    def service(self, mock_repo, session_store, agent_identity):
        """Create a DelegationService instance."""
        return DelegationService(
            session_store=session_store,
            repo_path=str(mock_repo),
            agent_identity=agent_identity
        )
    
    @pytest.fixture
    def delegation_session(self, session_store):
        """Create a delegation session."""
        session = Session(
            id=uuid4(),
            type=SessionType.DELEGATION,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="Test User", email="user@example.com"),
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            base_branch="main",
            turns=[],
            files_changed=[]
        )
        return session_store.create(session)
    
    def test_initialize_delegation(self, service, delegation_session):
        """Test initializing a delegation session."""
        session = service.initialize_delegation(delegation_session)
        
        assert session.worktree_path is not None
        assert session.session_branch is not None
        assert "agent/" in session.session_branch
        assert "testuser" in session.session_branch
        assert Path(session.worktree_path).exists()
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_initialize_delegation_with_slug(self, service, delegation_session):
        """Test initializing delegation with task slug."""
        session = service.initialize_delegation(
            delegation_session,
            task_slug="fix-bug-123"
        )
        
        assert "fix-bug-123" in session.session_branch
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_initialize_delegation_invalid_type(self, service, session_store):
        """Test initializing non-delegation session fails."""
        session = Session(
            id=uuid4(),
            type=SessionType.QUERY,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="testuser",
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            turns=[],
            files_changed=[]
        )
        session = session_store.create(session)
        
        with pytest.raises(ValueError, match="not a delegation session"):
            service.initialize_delegation(session)
    
    def test_initialize_delegation_no_base_branch(self, service, session_store):
        """Test initializing without base branch fails."""
        session = Session(
            id=uuid4(),
            type=SessionType.DELEGATION,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="testuser",
            user_identity=GitIdentity(name="User", email="user@example.com"),
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            turns=[],
            files_changed=[]
        )
        session = session_store.create(session)
        
        with pytest.raises(ValueError, match="Base branch is required"):
            service.initialize_delegation(session)
    
    def test_initialize_delegation_no_user_identity(self, service, session_store):
        """Test initializing without user identity fails."""
        session = Session(
            id=uuid4(),
            type=SessionType.DELEGATION,
            status=SessionStatus.ACTIVE,
            repo_name="test-repo",
            user_id="testuser",
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
            base_branch="main",
            turns=[],
            files_changed=[]
        )
        session = session_store.create(session)
        
        with pytest.raises(ValueError, match="User identity is required"):
            service.initialize_delegation(session)
    
    def test_commit_changes_no_changes(self, service, delegation_session):
        """Test committing when there are no changes."""
        session = service.initialize_delegation(delegation_session)
        
        # No changes, so commit should not create a commit
        result = service.commit_changes(session)
        
        assert result.commit_sha is None
        assert result.status == SessionStatus.ACTIVE
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_commit_changes_with_changes(self, service, delegation_session):
        """Test committing when there are changes."""
        session = service.initialize_delegation(delegation_session)
        
        # Make changes in worktree
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        # Commit changes
        result = service.commit_changes(session, message="Test commit")
        
        assert result.commit_sha is not None
        assert result.status == SessionStatus.COMMITTED
        assert len(result.files_changed) > 0
        assert "test.txt" in result.files_changed
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_commit_changes_auto_message(self, service, delegation_session):
        """Test committing with auto-generated message."""
        session = service.initialize_delegation(delegation_session)
        
        # Make changes
        (Path(session.worktree_path) / "file1.txt").write_text("Content 1")
        (Path(session.worktree_path) / "file2.txt").write_text("Content 2")
        
        # Commit without message
        result = service.commit_changes(session)
        
        assert result.commit_sha is not None
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_commit_changes_no_worktree(self, service, delegation_session):
        """Test committing without worktree fails."""
        with pytest.raises(ValueError, match="no worktree"):
            service.commit_changes(delegation_session)
    
    @patch('src.delegation.pr_manager.PRManager.create_pull_request')
    @patch('src.delegation.pr_manager.PRManager.push_branch')
    @pytest.mark.asyncio
    async def test_create_pull_request(
        self,
        mock_push,
        mock_create_pr,
        service,
        delegation_session
    ):
        """Test creating a pull request."""
        # Initialize and make changes
        session = service.initialize_delegation(delegation_session)
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        # Commit changes
        session = service.commit_changes(session)
        
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
        result = await service.create_pull_request(
            session=session,
            title="Test PR",
            body="Test description"
        )
        
        assert result.pr_url == "https://github.com/test/repo/pull/123"
        assert result.status == SessionStatus.PR_CREATED
        
        # Cleanup
        service.abandon_delegation(session)
    
    @patch('src.delegation.pr_manager.PRManager.create_pull_request')
    @patch('src.delegation.pr_manager.PRManager.push_branch')
    @pytest.mark.asyncio
    async def test_create_pull_request_auto_body(
        self,
        mock_push,
        mock_create_pr,
        service,
        delegation_session
    ):
        """Test creating PR with auto-generated body."""
        session = service.initialize_delegation(delegation_session)
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        session = service.commit_changes(session)
        
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
        
        # Create PR without body
        result = await service.create_pull_request(session=session, title="Test PR")
        
        # Verify auto-generated body was created
        mock_create_pr.assert_called_once()
        call_args = mock_create_pr.call_args
        assert call_args[1]['body'] is not None
        assert str(session.id) in call_args[1]['body']
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_create_pull_request_no_commit(self, service, delegation_session):
        """Test creating PR without commits fails."""
        session = service.initialize_delegation(delegation_session)
        
        with pytest.raises(ValueError, match="no commits"):
            service.create_pull_request(session=session, title="Test PR")
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_abandon_delegation(self, service, delegation_session):
        """Test abandoning a delegation session."""
        session = service.initialize_delegation(delegation_session)
        worktree_path = session.worktree_path
        
        # Abandon
        result = service.abandon_delegation(session, delete_branch=True)
        
        assert result.status == SessionStatus.ABANDONED
        assert not Path(worktree_path).exists()
    
    def test_abandon_delegation_keep_branch(self, service, delegation_session, mock_repo):
        """Test abandoning without deleting branch."""
        session = service.initialize_delegation(delegation_session)
        branch_name = session.session_branch
        
        # Abandon but keep branch
        result = service.abandon_delegation(session, delete_branch=False)
        
        assert result.status == SessionStatus.ABANDONED
        
        # Verify branch still exists
        branches_output = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=mock_repo,
            capture_output=True,
            text=True
        )
        assert branch_name in branches_output.stdout
        
        # Cleanup branch manually
        subprocess.run(['git', 'branch', '-D', branch_name], cwd=mock_repo, capture_output=True)
    
    def test_get_delegation_status(self, service, delegation_session):
        """Test getting delegation status."""
        session = service.initialize_delegation(delegation_session)
        
        status = service.get_delegation_status(session)
        
        assert status['session_id'] == str(session.id)
        assert status['status'] == SessionStatus.ACTIVE.value
        assert status['base_branch'] == "main"
        assert status['session_branch'] is not None
        assert status['worktree_path'] is not None
        assert status['has_uncommitted_changes'] is False
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_get_delegation_status_with_changes(self, service, delegation_session):
        """Test getting status with uncommitted changes."""
        session = service.initialize_delegation(delegation_session)
        
        # Make changes
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        status = service.get_delegation_status(session)
        
        assert status['has_uncommitted_changes'] is True
        
        # Cleanup
        service.abandon_delegation(session)
    
    def test_get_delegation_status_after_commit(self, service, delegation_session):
        """Test getting status after committing."""
        session = service.initialize_delegation(delegation_session)
        
        # Make and commit changes
        test_file = Path(session.worktree_path) / "test.txt"
        test_file.write_text("Test content")
        session = service.commit_changes(session)
        
        status = service.get_delegation_status(session)
        
        assert status['status'] == SessionStatus.COMMITTED.value
        assert status['commit_sha'] is not None
        assert len(status['files_changed']) > 0
        assert status['has_uncommitted_changes'] is False
        
        # Cleanup
        service.abandon_delegation(session)
