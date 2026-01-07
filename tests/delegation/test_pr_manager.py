"""Tests for PRManager."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

from src.delegation.pr_manager import PRManager
from src.delegation.worktree_manager import WorktreeManager
from src.delegation.commit_manager import CommitManager
from src.session.models import GitIdentity
from src.integrations.platforms.base import PRResult


class TestPRManager:
    """Test PRManager functionality."""
    
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
    def pr_manager(self, mock_repo):
        """Create a PRManager instance."""
        return PRManager(str(mock_repo))
    
    @pytest.fixture
    def worktree_with_commit(self, mock_repo):
        """Create a test worktree with a commit."""
        wt_manager = WorktreeManager(str(mock_repo))
        cm_manager = CommitManager(str(mock_repo))
        session_id = uuid4()
        
        wt_path, branch_name = wt_manager.create_delegation_worktree(
            repo_path=str(mock_repo),
            base_branch="main",
            session_id=session_id,
            user_id="testuser"
        )
        
        # Create a commit
        test_file = Path(wt_path) / "test.txt"
        test_file.write_text("Test content")
        
        user_identity = GitIdentity(name="Test User", email="user@example.com")
        agent_identity = GitIdentity(name="Test Agent", email="agent@example.com")
        
        cm_manager.commit_delegation_changes(
            worktree_path=wt_path,
            user_identity=user_identity,
            agent_identity=agent_identity,
            message="Test commit"
        )
        
        yield wt_path, branch_name
        
        # Cleanup
        wt_manager.cleanup_worktree(wt_path, delete_branch=True)
    
    @pytest.mark.asyncio
    async def test_platform_detection(self, pr_manager):
        """Test that platform detection works."""
        with patch.object(pr_manager, '_get_remote_url', return_value='git@gitlab.com:user/repo.git'):
            platform = pr_manager._detect_platform()
            assert platform.get_platform_name() in ["GitLab", "GitLab (self-hosted)"]
    
    @pytest.mark.asyncio
    async def test_set_platform_config(self, pr_manager):
        """Test setting platform configuration."""
        config = {"token": "test-token"}
        pr_manager.set_platform_config(config)
        assert pr_manager._platform_config == config
        assert pr_manager._platform is None  # Should reset platform
    
    @pytest.mark.asyncio
    async def test_extract_repo_identifier_gitlab(self, pr_manager):
        """Test extracting repo identifier for GitLab."""
        from src.integrations.platforms.gitlab import GitLab
        
        platform = GitLab()
        
        # HTTPS URL
        repo = pr_manager._extract_repo_identifier(
            "https://gitlab.com/namespace/project.git",
            platform
        )
        assert repo == "namespace/project"
        
        # SSH URL
        repo = pr_manager._extract_repo_identifier(
            "git@gitlab.com:namespace/project.git",
            platform
        )
        assert repo == "namespace/project"
    
    @pytest.mark.asyncio
    async def test_extract_repo_identifier_azure_devops(self, pr_manager):
        """Test extracting repo identifier for Azure DevOps."""
        from src.integrations.platforms.azure_devops import AzureDevOps
        
        platform = AzureDevOps(organization="myorg")
        
        # HTTPS URL
        repo = pr_manager._extract_repo_identifier(
            "https://dev.azure.com/myorg/myproject/_git/myrepo",
            platform
        )
        assert repo == "myproject/myrepo"
        
        # SSH URL
        repo = pr_manager._extract_repo_identifier(
            "git@ssh.dev.azure.com:v3/myorg/myproject/myrepo",
            platform
        )
        assert repo == "myproject/myrepo"
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_pull_request_with_platform_api(self, mock_run, pr_manager, worktree_with_commit):
        """Test creating PR using platform API."""
        wt_path, branch_name = worktree_with_commit
        
        # Mock successful push
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        # Mock platform detection and PR creation
        mock_platform = MagicMock()
        mock_platform.get_platform_name.return_value = "GitLab"
        mock_platform.create_pull_request = AsyncMock(return_value=PRResult(
            status="success",
            pr_id="123",
            pr_number=123,
            pr_url="https://gitlab.com/user/repo/-/merge_requests/123",
            message="MR created successfully"
        ))
        
        with patch.object(pr_manager, '_detect_platform', return_value=mock_platform):
            with patch.object(pr_manager, '_get_remote_url', return_value='git@gitlab.com:user/repo.git'):
                result = await pr_manager.create_pull_request(
                    worktree_path=wt_path,
                    branch_name=branch_name,
                    base_branch="main",
                    title="Test MR",
                    body="Test MR body",
                    repo_identifier="user/repo"
                )
        
        assert result["status"] == "success"
        assert result["pr_url"] == "https://gitlab.com/user/repo/-/merge_requests/123"
        assert result["platform"] == "GitLab"
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_pull_request_manual_fallback(self, mock_run, pr_manager, worktree_with_commit):
        """Test creating PR falls back to manual instructions."""
        wt_path, branch_name = worktree_with_commit
        
        # Mock successful push
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        # Mock platform detection (generic platform)
        mock_platform = MagicMock()
        mock_platform.get_platform_name.return_value = "Generic Git Platform"
        mock_platform.create_pull_request = AsyncMock(return_value=PRResult(
            status="manual",
            message="Manual PR creation required",
            instructions="Push branch and create PR manually..."
        ))
        
        with patch.object(pr_manager, '_detect_platform', return_value=mock_platform):
            with patch.object(pr_manager, '_get_remote_url', return_value='git@custom.com:user/repo.git'):
                result = await pr_manager.create_pull_request(
                    worktree_path=wt_path,
                    branch_name=branch_name,
                    base_branch="main",
                    title="Test PR",
                    repo_identifier="user/repo"
                )
        
        assert result["status"] == "manual"
        assert result["instructions"] is not None
        assert result["platform"] == "Generic Git Platform"
    
    @pytest.mark.asyncio
    async def test_get_pr_details(self, pr_manager):
        """Test getting PR details via platform API."""
        from src.integrations.platforms.base import PRInfo
        
        mock_platform = MagicMock()
        mock_platform.get_pull_request = AsyncMock(return_value=PRInfo(
            id="123",
            number=123,
            title="Test PR",
            body="Test description",
            state="open",
            head_branch="feature",
            base_branch="main",
            url="https://gitlab.com/user/repo/-/merge_requests/123",
            author="testuser"
        ))
        
        with patch.object(pr_manager, '_detect_platform', return_value=mock_platform):
            details = await pr_manager.get_pr_details("user/repo", "123")
        
        assert details["id"] == "123"
        assert details["number"] == 123
        assert details["title"] == "Test PR"
        assert details["state"] == "open"
    
    def test_check_gh_cli_available_not_installed(self, pr_manager):
        """Test checking for gh CLI when not installed."""
        with patch.object(pr_manager, '_run_command', side_effect=RuntimeError("gh not found")):
            result = pr_manager.check_gh_cli_available()
            assert result is False
    
    def test_check_gh_cli_available_installed(self, pr_manager):
        """Test checking for gh CLI when installed and authenticated."""
        with patch.object(pr_manager, '_run_command', return_value="gh version 2.0.0"):
            result = pr_manager.check_gh_cli_available()
            assert result is True
    
    def test_generate_pr_body_minimal(self, pr_manager):
        """Test generating PR body with minimal information."""
        session_id = str(uuid4())
        files_changed = ["file1.txt", "file2.txt"]
        
        body = pr_manager.generate_pr_body(
            session_id=session_id,
            files_changed=files_changed
        )
        
        assert session_id in body
        assert "2" in body  # Number of files
        assert "file1.txt" in body
        assert "file2.txt" in body
        assert "Agent CLI Orchestrator" in body
    
    def test_generate_pr_body_with_summary(self, pr_manager):
        """Test generating PR body with summary."""
        session_id = str(uuid4())
        files_changed = ["file1.txt"]
        summary = "This PR implements feature X"
        
        body = pr_manager.generate_pr_body(
            session_id=session_id,
            files_changed=files_changed,
            summary=summary
        )
        
        assert summary in body
        assert session_id in body
    
    def test_generate_pr_body_many_files(self, pr_manager):
        """Test generating PR body with many files (should truncate)."""
        session_id = str(uuid4())
        files_changed = [f"file{i}.txt" for i in range(30)]
        
        body = pr_manager.generate_pr_body(
            session_id=session_id,
            files_changed=files_changed
        )
        
        assert "30" in body  # Total count
        assert "... and 10 more files" in body  # Truncation message
    
    @patch('subprocess.run')
    def test_push_branch_success(self, mock_run, pr_manager, worktree_with_commit):
        """Test pushing branch successfully."""
        wt_path, branch_name = worktree_with_commit
        
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        # Should not raise
        pr_manager.push_branch(wt_path, branch_name)
        
        # Verify git push was called
        assert any('push' in str(call) for call in mock_run.call_args_list)
    
    @patch('subprocess.run')
    def test_push_branch_force(self, mock_run, pr_manager, worktree_with_commit):
        """Test force pushing branch."""
        wt_path, branch_name = worktree_with_commit
        
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        
        pr_manager.push_branch(wt_path, branch_name, force=True)
        
        # Verify --force was included
        push_calls = [call for call in mock_run.call_args_list if 'push' in str(call)]
        assert any('--force' in str(call) for call in push_calls)
    
    
    @patch('subprocess.run')
    def test_get_pr_status(self, mock_run, pr_manager, worktree_with_commit):
        """Test getting PR status (legacy GitHub CLI method)."""
        wt_path, _ = worktree_with_commit
        
        mock_run.return_value = MagicMock(
            stdout='{"state": "OPEN", "title": "Test PR", "url": "https://github.com/test/repo/pull/123", "number": 123, "headRefName": "test-branch", "baseRefName": "main"}',
            stderr="",
            returncode=0
        )
        
        status = pr_manager.get_pr_status(wt_path, 123)
        
        assert status['state'] == 'OPEN'
        assert status['title'] == 'Test PR'
        assert status['number'] == 123
    
    @patch('subprocess.run')
    def test_get_pr_status_failure(self, mock_run, pr_manager, worktree_with_commit):
        """Test getting PR status when it fails (legacy GitHub CLI method)."""
        wt_path, _ = worktree_with_commit
        
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['gh', 'pr', 'view'], stderr="PR not found"
        )
        
        with pytest.raises(RuntimeError, match="Failed to get PR status"):
            pr_manager.get_pr_status(wt_path, 999)

