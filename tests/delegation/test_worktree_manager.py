"""Tests for WorktreeManager."""

import pytest
import subprocess
from pathlib import Path
from uuid import uuid4

from src.delegation.worktree_manager import WorktreeManager


class TestWorktreeManager:
    """Test WorktreeManager functionality."""
    
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
        
        # Create a branch to use as base
        subprocess.run(['git', 'branch', 'main'], cwd=repo_dir, check=True, capture_output=True)
        
        return repo_dir
    
    @pytest.fixture
    def manager(self, mock_repo):
        """Create a WorktreeManager instance."""
        return WorktreeManager(str(mock_repo))
    
    def test_create_delegation_worktree(self, manager, mock_repo):
        """Test creating a delegation worktree."""
        session_id = uuid4()
        user_id = "testuser"
        base_branch = "main"
        
        worktree_path, branch_name = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch=base_branch,
            session_id=session_id,
            user_id=user_id
        )
        
        # Verify worktree was created
        assert Path(worktree_path).exists()
        assert Path(worktree_path).is_dir()
        
        # Verify branch name format
        assert branch_name.startswith(f"agent/{user_id}/")
        assert str(session_id)[:8] in branch_name
        
        # Cleanup
        manager.cleanup_worktree(worktree_path, delete_branch=True)
    
    def test_create_delegation_worktree_with_slug(self, manager, mock_repo):
        """Test creating a delegation worktree with task slug."""
        session_id = uuid4()
        user_id = "testuser"
        base_branch = "main"
        task_slug = "fix-bug-123"
        
        worktree_path, branch_name = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch=base_branch,
            session_id=session_id,
            user_id=user_id,
            task_slug=task_slug
        )
        
        # Verify branch name includes slug
        assert task_slug in branch_name
        assert branch_name == f"agent/{user_id}/{str(session_id)[:8]}-{task_slug}"
        
        # Cleanup
        manager.cleanup_worktree(worktree_path, delete_branch=True)
    
    def test_create_temp_worktree(self, manager, mock_repo):
        """Test creating a temporary worktree for research."""
        session_id = uuid4()
        
        # Get current commit SHA
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=mock_repo,
            capture_output=True,
            text=True,
            check=True
        )
        commit_sha = result.stdout.strip()
        
        worktree_path = manager.create_temp_worktree(
            repo_path=str(mock_repo),
            commit_sha=commit_sha,
            session_id=session_id
        )
        
        # Verify worktree was created
        assert Path(worktree_path).exists()
        assert "research" in worktree_path
        
        # Cleanup
        manager.cleanup_worktree(worktree_path)
    
    def test_cleanup_worktree(self, manager, mock_repo):
        """Test cleaning up a worktree."""
        session_id = uuid4()
        user_id = "testuser"
        
        worktree_path, branch_name = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id=user_id
        )
        
        # Verify it exists
        assert Path(worktree_path).exists()
        
        # Clean up without deleting branch
        manager.cleanup_worktree(worktree_path, delete_branch=False)
        
        # Verify worktree is removed
        assert not Path(worktree_path).exists()
        
        # Verify branch still exists
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=mock_repo,
            capture_output=True,
            text=True
        )
        assert branch_name in result.stdout
        
        # Cleanup branch
        subprocess.run(['git', 'branch', '-D', branch_name], cwd=mock_repo, capture_output=True)
    
    def test_cleanup_worktree_with_branch_deletion(self, manager, mock_repo):
        """Test cleaning up a worktree and deleting the branch."""
        session_id = uuid4()
        user_id = "testuser"
        
        worktree_path, branch_name = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id=user_id
        )
        
        # Clean up with branch deletion
        manager.cleanup_worktree(worktree_path, delete_branch=True)
        
        # Verify worktree and branch are removed
        assert not Path(worktree_path).exists()
        
        result = subprocess.run(
            ['git', 'branch', '--list', branch_name],
            cwd=mock_repo,
            capture_output=True,
            text=True
        )
        assert branch_name not in result.stdout
    
    def test_cleanup_nonexistent_worktree(self, manager, mock_repo):
        """Test cleaning up a worktree that doesn't exist."""
        # Should not raise an error
        manager.cleanup_worktree("/nonexistent/path")
    
    def test_list_worktrees(self, manager, mock_repo):
        """Test listing worktrees."""
        session_id = uuid4()
        
        # Initially should have just the main worktree
        worktrees = manager.list_worktrees()
        initial_count = len(worktrees)
        
        # Create a delegation worktree
        worktree_path, _ = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id="testuser"
        )
        
        # List should now include the new worktree
        worktrees = manager.list_worktrees()
        assert len(worktrees) == initial_count + 1
        
        # Find our worktree in the list
        found = False
        for wt in worktrees:
            if worktree_path in wt.get('path', ''):
                found = True
                break
        assert found, "Created worktree not found in list"
        
        # Cleanup
        manager.cleanup_worktree(worktree_path, delete_branch=True)
    
    def test_create_worktree_invalid_base_branch(self, manager, mock_repo):
        """Test creating worktree with invalid base branch."""
        session_id = uuid4()
        
        with pytest.raises(RuntimeError):
            manager.create_delegation_worktree(
                repo_path=str(mock_repo),
                base_branch="nonexistent-branch",
                session_id=session_id,
                user_id="testuser"
            )
    
    def test_worktree_isolation(self, manager, mock_repo):
        """Test that worktrees are properly isolated."""
        session_id = uuid4()
        
        # Create worktree
        worktree_path, _ = manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id="testuser"
        )
        
        # Modify file in worktree
        test_file = Path(worktree_path) / "test.txt"
        test_file.write_text("Test content")
        
        # Verify file doesn't exist in main repo
        main_test_file = Path(mock_repo) / "test.txt"
        assert not main_test_file.exists()
        
        # Cleanup
        manager.cleanup_worktree(worktree_path, delete_branch=True)
