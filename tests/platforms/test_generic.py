"""Tests for Generic platform fallback."""

import pytest
from src.integrations.platforms.generic import GenericPlatform


class TestGenericPlatform:
    """Tests for GenericPlatform."""
    
    def test_initialization(self):
        """Test GenericPlatform initialization."""
        platform = GenericPlatform(remote_url="https://git.company.com/repo.git")
        assert platform.remote_url == "https://git.company.com/repo.git"
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = GenericPlatform()
        assert platform.get_platform_name() == "Generic Git Platform"
    
    def test_detect_from_url(self):
        """Test URL detection (always False)."""
        assert not GenericPlatform.detect_from_url("https://any-git-server.com/repo.git")
        assert not GenericPlatform.detect_from_url("git@github.com:user/repo.git")
    
    @pytest.mark.asyncio
    async def test_create_pull_request_returns_manual_instructions(self):
        """Test that PR creation returns manual instructions."""
        platform = GenericPlatform(remote_url="https://git.company.com/repo.git")
        
        result = await platform.create_pull_request(
            "team/repository",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
            draft=False,
        )
        
        assert result.status == "manual"
        assert "Manual Pull Request Creation Required" in result.instructions
        assert "feature-branch" in result.instructions
        assert "main" in result.instructions
        assert "Test PR" in result.instructions
        assert "git push origin feature-branch" in result.instructions
    
    @pytest.mark.asyncio
    async def test_create_pull_request_draft_instructions(self):
        """Test manual instructions for draft PR."""
        platform = GenericPlatform()
        
        result = await platform.create_pull_request(
            "team/repository",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
            draft=True,
        )
        
        assert result.status == "manual"
        assert "Mark as draft" in result.instructions
    
    @pytest.mark.asyncio
    async def test_get_pull_request_not_implemented(self):
        """Test that get_pull_request raises NotImplementedError."""
        platform = GenericPlatform()
        
        with pytest.raises(NotImplementedError) as excinfo:
            await platform.get_pull_request("team/repository", "123")
        
        assert "not supported for generic platform" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_list_pull_requests_not_implemented(self):
        """Test that list_pull_requests raises NotImplementedError."""
        platform = GenericPlatform()
        
        with pytest.raises(NotImplementedError) as excinfo:
            await platform.list_pull_requests("team/repository")
        
        assert "not supported for generic platform" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_add_pr_comment_not_implemented(self):
        """Test that add_pr_comment raises NotImplementedError."""
        platform = GenericPlatform()
        
        with pytest.raises(NotImplementedError) as excinfo:
            await platform.add_pr_comment("team/repository", "123", "Test comment")
        
        assert "not supported for generic platform" in str(excinfo.value)
