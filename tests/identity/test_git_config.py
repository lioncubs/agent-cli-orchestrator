"""Tests for Git configuration manager."""

import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path

from src.identity.git_config import GitConfigManager
from src.session.models import GitIdentity


class TestGitConfigManager:
    """Test Git configuration manager."""
    
    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        temp_path = tempfile.mkdtemp()
        
        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=temp_path,
            check=True,
            capture_output=True
        )
        
        # Create initial commit to have a valid repo
        test_file = Path(temp_path) / "test.txt"
        test_file.write_text("test")
        
        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=temp_path,
            check=True,
            capture_output=True
        )
        
        # Set temporary identity for initial commit
        subprocess.run(
            ["git", "config", "--local", "user.name", "Test Init"],
            cwd=temp_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "--local", "user.email", "init@test.com"],
            cwd=temp_path,
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=temp_path,
            check=True,
            capture_output=True
        )
        
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def manager(self, temp_git_repo):
        """Create a Git config manager."""
        return GitConfigManager(repo_path=temp_git_repo)
    
    def test_set_local_identity(self, manager, temp_git_repo):
        """Test setting local Git identity."""
        identity = GitIdentity(name="John Doe", email="john@example.com")
        
        success = manager.set_local_identity(identity)
        assert success is True
        
        # Verify by reading git config
        name_result = subprocess.run(
            ["git", "config", "--local", "user.name"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
            check=True
        )
        assert name_result.stdout.strip() == "John Doe"
        
        email_result = subprocess.run(
            ["git", "config", "--local", "user.email"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
            check=True
        )
        assert email_result.stdout.strip() == "john@example.com"
    
    def test_get_local_identity(self, manager):
        """Test getting local Git identity."""
        # Set identity first
        identity = GitIdentity(name="Jane Smith", email="jane@example.com")
        manager.set_local_identity(identity)
        
        # Get identity
        retrieved = manager.get_local_identity()
        
        assert retrieved is not None
        assert retrieved.name == "Jane Smith"
        assert retrieved.email == "jane@example.com"
    
    def test_get_local_identity_not_set(self, temp_git_repo):
        """Test getting identity when not set."""
        # Create a fresh manager on a repo without identity
        temp_path = tempfile.mkdtemp()
        subprocess.run(["git", "init"], cwd=temp_path, check=True, capture_output=True)
        
        manager = GitConfigManager(repo_path=temp_path)
        identity = manager.get_local_identity()
        
        # Should return None when not configured
        assert identity is None
        
        shutil.rmtree(temp_path, ignore_errors=True)
    
    def test_unset_local_identity(self, manager):
        """Test removing local Git identity."""
        # Set identity first
        identity = GitIdentity(name="Test User", email="test@example.com")
        manager.set_local_identity(identity)
        
        # Verify it's set
        assert manager.get_local_identity() is not None
        
        # Unset identity
        success = manager.unset_local_identity()
        assert success is True
        
        # Verify it's gone
        assert manager.get_local_identity() is None
    
    def test_create_commit_env(self):
        """Test creating commit environment variables."""
        identity = GitIdentity(name="Alice", email="alice@example.com")
        
        env = GitConfigManager.create_commit_env(identity)
        
        assert env["GIT_AUTHOR_NAME"] == "Alice"
        assert env["GIT_AUTHOR_EMAIL"] == "alice@example.com"
        assert env["GIT_COMMITTER_NAME"] == "Alice"
        assert env["GIT_COMMITTER_EMAIL"] == "alice@example.com"
    
    def test_set_worktree_identity(self, temp_git_repo):
        """Test setting identity in a worktree."""
        # Create a worktree
        worktree_path = Path(temp_git_repo).parent / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "HEAD"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True
        )
        
        # Set identity in worktree
        manager = GitConfigManager(repo_path=temp_git_repo)
        identity = GitIdentity(name="Worktree User", email="worktree@example.com")
        
        success = manager.set_worktree_identity(str(worktree_path), identity)
        assert success is True
        
        # Verify by reading git config in worktree
        name_result = subprocess.run(
            ["git", "config", "--local", "user.name"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        assert name_result.stdout.strip() == "Worktree User"
        
        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=temp_git_repo,
            check=False,
            capture_output=True
        )
