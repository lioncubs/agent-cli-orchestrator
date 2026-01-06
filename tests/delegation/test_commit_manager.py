"""Tests for CommitManager."""

import pytest
import subprocess
from pathlib import Path
from uuid import uuid4

from src.delegation.commit_manager import CommitManager
from src.delegation.worktree_manager import WorktreeManager
from src.session.models import GitIdentity


class TestCommitManager:
    """Test CommitManager functionality."""
    
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
    def worktree_path(self, mock_repo):
        """Create a test worktree."""
        manager = WorktreeManager(str(mock_repo))
        session_id = uuid4()
        
        wt_path, branch_name = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id="testuser"
        )
        
        yield wt_path
        
        # Cleanup
        manager.cleanup_worktree(wt_path, delete_branch=True)
    
    @pytest.fixture
    def commit_manager(self, mock_repo):
        """Create a CommitManager instance."""
        return CommitManager(str(mock_repo))
    
    @pytest.fixture
    def user_identity(self):
        """Create a test user identity."""
        return GitIdentity(name="Test User", email="user@example.com")
    
    @pytest.fixture
    def agent_identity(self):
        """Create a test agent identity."""
        return GitIdentity(name="Test Agent", email="agent@example.com")
    
    def test_get_changed_files_empty(self, commit_manager, worktree_path):
        """Test getting changed files when there are none."""
        changed = commit_manager.get_changed_files(worktree_path)
        assert changed == []
    
    def test_get_changed_files_with_modifications(self, commit_manager, worktree_path):
        """Test getting changed files with modifications."""
        # Modify a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("New content")
        
        changed = commit_manager.get_changed_files(worktree_path)
        assert len(changed) > 0
        assert "test.txt" in changed
    
    def test_get_changed_files_with_multiple_changes(self, commit_manager, worktree_path):
        """Test getting changed files with multiple modifications."""
        # Create and modify multiple files
        (Path(worktree_path) / "file1.txt").write_text("Content 1")
        (Path(worktree_path) / "file2.txt").write_text("Content 2")
        (Path(worktree_path) / "file3.txt").write_text("Content 3")
        
        changed = commit_manager.get_changed_files(worktree_path)
        assert len(changed) == 3
        assert "file1.txt" in changed
        assert "file2.txt" in changed
        assert "file3.txt" in changed
    
    def test_commit_delegation_changes_no_changes(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test committing when there are no changes."""
        commit_sha = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Test commit"
        )
        
        assert commit_sha is None
    
    def test_commit_delegation_changes_with_changes(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test committing changes."""
        # Create a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        commit_sha = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Test commit"
        )
        
        assert commit_sha is not None
        assert len(commit_sha) == 40  # SHA-1 hash length
    
    def test_commit_delegation_changes_auto_message(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test committing with auto-generated message."""
        # Create files
        (Path(worktree_path) / "file1.txt").write_text("Content 1")
        (Path(worktree_path) / "file2.txt").write_text("Content 2")
        
        commit_sha = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity
        )
        
        assert commit_sha is not None
        
        # Verify commit message
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        assert "Delegation changes" in result.stdout
        assert "2 file(s)" in result.stdout
    
    def test_commit_delegation_changes_identity_preservation(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test that author and committer identities are properly set."""
        # Create a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        commit_sha = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Test commit"
        )
        
        # Verify author identity
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%an <%ae>'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        assert user_identity.name in result.stdout
        assert user_identity.email in result.stdout
        
        # Verify committer identity
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%cn <%ce>'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        assert agent_identity.name in result.stdout
        assert agent_identity.email in result.stdout
    
    def test_get_commit_info(self, commit_manager, worktree_path, user_identity, agent_identity):
        """Test getting commit information."""
        # Create and commit a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        commit_sha = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Test commit message"
        )
        
        # Get commit info
        info = commit_manager.get_commit_info(worktree_path, commit_sha)
        
        assert info['sha'] == commit_sha
        assert user_identity.name in info['author']
        assert user_identity.email in info['author']
        assert agent_identity.name in info['committer']
        assert agent_identity.email in info['committer']
        assert "Test commit message" in info['message']
        assert info['date'] is not None
    
    def test_has_uncommitted_changes_false(self, commit_manager, worktree_path):
        """Test checking for uncommitted changes when there are none."""
        has_changes = commit_manager.has_uncommitted_changes(worktree_path)
        assert has_changes is False
    
    def test_has_uncommitted_changes_true(self, commit_manager, worktree_path):
        """Test checking for uncommitted changes when there are some."""
        # Create a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        has_changes = commit_manager.has_uncommitted_changes(worktree_path)
        assert has_changes is True
    
    def test_has_uncommitted_changes_after_commit(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test that uncommitted changes check works after committing."""
        # Create and commit a file
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity
        )
        
        # Should have no uncommitted changes after commit
        has_changes = commit_manager.has_uncommitted_changes(worktree_path)
        assert has_changes is False
        
        # Modify file again
        test_file.write_text("Modified content")
        
        # Should have uncommitted changes now
        has_changes = commit_manager.has_uncommitted_changes(worktree_path)
        assert has_changes is True
    
    def test_commit_multiple_times(
        self,
        commit_manager,
        worktree_path,
        user_identity,
        agent_identity
    ):
        """Test making multiple commits in sequence."""
        # First commit
        (Path(worktree_path) / "file1.txt").write_text("Content 1")
        commit1 = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="First commit"
        )
        
        # Second commit
        (Path(worktree_path) / "file2.txt").write_text("Content 2")
        commit2 = commit_manager.commit_delegation_changes(
            worktree_path=worktree_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Second commit"
        )
        
        assert commit1 is not None
        assert commit2 is not None
        assert commit1 != commit2
