"""Tests for git_operations module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from git_operations import GitOperations


class TestGitOperations:
    """Test suite for GitOperations class."""
    
    def test_init(self):
        """Test GitOperations initialization."""
        git_ops = GitOperations("/test/path")
        assert str(git_ops.repo_path) == "/test/path"
    
    def test_init_default_path(self):
        """Test GitOperations with default path."""
        git_ops = GitOperations()
        assert str(git_ops.repo_path) == "."
    
    @patch('git_operations.subprocess.run')
    def test_get_current_branch_success(self, mock_run):
        """Test getting current branch successfully."""
        mock_run.return_value = Mock(
            stdout="main\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        branch = git_ops.get_current_branch()
        
        assert branch == "main"
        mock_run.assert_called_once()
    
    @patch('git_operations.subprocess.run')
    def test_get_current_branch_failure(self, mock_run):
        """Test get current branch with git error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git', stderr="fatal: not a git repository"
        )
        
        git_ops = GitOperations()
        
        with pytest.raises(RuntimeError) as exc_info:
            git_ops.get_current_branch()
        
        assert "Failed to get current branch" in str(exc_info.value)
    
    @patch('git_operations.subprocess.run')
    def test_switch_branch_success(self, mock_run):
        """Test switching branch successfully."""
        mock_run.return_value = Mock(
            stdout="Switched to branch 'develop'\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        result = git_ops.switch_branch("develop")
        
        assert result["status"] == "success"
        assert result["branch"] == "develop"
        assert "Switched to branch" in result["message"]
    
    @patch('git_operations.subprocess.run')
    def test_switch_branch_invalid(self, mock_run):
        """Test switching to invalid branch."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git', stderr="error: pathspec 'invalid' did not match"
        )
        
        git_ops = GitOperations()
        
        with pytest.raises(RuntimeError) as exc_info:
            git_ops.switch_branch("invalid")
        
        assert "Failed to switch branch" in str(exc_info.value)
    
    @patch('git_operations.subprocess.run')
    def test_list_worktrees_single(self, mock_run):
        """Test listing single worktree."""
        mock_output = """worktree /path/to/repo
HEAD abc123def456
branch refs/heads/main
"""
        mock_run.return_value = Mock(
            stdout=mock_output,
            returncode=0
        )
        
        git_ops = GitOperations()
        worktrees = git_ops.list_worktrees()
        
        assert len(worktrees) == 1
        assert worktrees[0]["path"] == "/path/to/repo"
        assert worktrees[0]["branch"] == "main"
        assert worktrees[0]["HEAD"] == "abc123def456"
    
    @patch('git_operations.subprocess.run')
    def test_list_worktrees_multiple(self, mock_run):
        """Test listing multiple worktrees."""
        mock_output = """worktree /path/to/repo
HEAD abc123
branch refs/heads/main

worktree /path/to/worktrees/feature
HEAD def456
branch refs/heads/feature/new
"""
        mock_run.return_value = Mock(
            stdout=mock_output,
            returncode=0
        )
        
        git_ops = GitOperations()
        worktrees = git_ops.list_worktrees()
        
        assert len(worktrees) == 2
        assert worktrees[0]["branch"] == "main"
        assert worktrees[1]["branch"] == "feature/new"
    
    @patch('git_operations.subprocess.run')
    def test_list_worktrees_failure(self, mock_run):
        """Test list worktrees with git error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git', stderr="fatal: error"
        )
        
        git_ops = GitOperations()
        
        with pytest.raises(RuntimeError) as exc_info:
            git_ops.list_worktrees()
        
        assert "Failed to list worktrees" in str(exc_info.value)
    
    @patch('git_operations.subprocess.run')
    def test_create_worktree_success(self, mock_run):
        """Test creating worktree successfully."""
        mock_run.return_value = Mock(
            stdout="Preparing worktree\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        result = git_ops.create_worktree("/path/to/worktree", "feature-branch")
        
        assert result["status"] == "success"
        assert result["path"] == "/path/to/worktree"
        assert result["branch"] == "feature-branch"
    
    @patch('git_operations.subprocess.run')
    def test_create_worktree_with_new_branch(self, mock_run):
        """Test creating worktree with new branch."""
        mock_run.return_value = Mock(
            stdout="Preparing worktree\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        result = git_ops.create_worktree(
            "/path/to/worktree",
            "new-branch",
            create_branch=True
        )
        
        assert result["status"] == "success"
        mock_run.assert_called_once()
        # Verify -b flag was used
        call_args = mock_run.call_args[0][0]
        assert '-b' in call_args
    
    @patch('git_operations.subprocess.run')
    def test_create_worktree_failure(self, mock_run):
        """Test create worktree failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git', stderr="fatal: '/path' already exists"
        )
        
        git_ops = GitOperations()
        
        with pytest.raises(RuntimeError) as exc_info:
            git_ops.create_worktree("/path", "branch")
        
        assert "Failed to create worktree" in str(exc_info.value)
    
    @patch('git_operations.subprocess.run')
    def test_get_repository_name_https(self, mock_run):
        """Test getting repository name from HTTPS URL."""
        mock_run.return_value = Mock(
            stdout="https://github.com/user/test-repo.git\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        repo_name = git_ops.get_repository_name()
        
        assert repo_name == "test-repo"
    
    @patch('git_operations.subprocess.run')
    def test_get_repository_name_ssh(self, mock_run):
        """Test getting repository name from SSH URL."""
        mock_run.return_value = Mock(
            stdout="git@github.com:user/my-repo.git\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        repo_name = git_ops.get_repository_name()
        
        assert repo_name == "my-repo"
    
    @patch('git_operations.subprocess.run')
    def test_get_repository_name_no_git_extension(self, mock_run):
        """Test getting repository name without .git extension."""
        mock_run.return_value = Mock(
            stdout="https://github.com/user/repo-name\n",
            returncode=0
        )
        
        git_ops = GitOperations()
        repo_name = git_ops.get_repository_name()
        
        assert repo_name == "repo-name"
    
    @patch('git_operations.subprocess.run')
    def test_get_repository_name_failure(self, mock_run):
        """Test get repository name with git error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, 'git', stderr="fatal: not a git repository"
        )
        
        git_ops = GitOperations()
        repo_name = git_ops.get_repository_name()
        
        assert repo_name == "unknown"
    
    @patch('git_operations.subprocess.run')
    def test_get_repository_name_empty(self, mock_run):
        """Test get repository name with empty URL."""
        mock_run.return_value = Mock(
            stdout="",
            returncode=0
        )
        
        git_ops = GitOperations()
        repo_name = git_ops.get_repository_name()
        
        assert repo_name == "unknown"