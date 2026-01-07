"""Tests for platform base classes and interfaces."""

import pytest
from src.integrations.platforms.base import GitPlatform, PRResult, PRInfo


def test_pr_info_model():
    """Test PRInfo model creation and validation."""
    pr = PRInfo(
        id="123",
        number=123,
        title="Test PR",
        body="Test description",
        state="open",
        head_branch="feature",
        base_branch="main",
        url="https://example.com/pr/123",
        author="testuser",
        draft=False,
    )
    
    assert pr.id == "123"
    assert pr.number == 123
    assert pr.title == "Test PR"
    assert pr.state == "open"
    assert pr.head_branch == "feature"
    assert pr.base_branch == "main"


def test_pr_result_model_success():
    """Test PRResult model for successful PR creation."""
    result = PRResult(
        status="success",
        pr_id="456",
        pr_number=456,
        pr_url="https://example.com/pr/456",
        message="PR created successfully",
    )
    
    assert result.status == "success"
    assert result.pr_id == "456"
    assert result.pr_number == 456
    assert result.pr_url == "https://example.com/pr/456"
    assert result.error is None
    assert result.instructions is None


def test_pr_result_model_error():
    """Test PRResult model for failed PR creation."""
    result = PRResult(
        status="error",
        message="Failed to create PR",
        error="Authentication failed",
        instructions="Please configure your token",
    )
    
    assert result.status == "error"
    assert result.pr_id is None
    assert result.error == "Authentication failed"
    assert result.instructions == "Please configure your token"


def test_pr_result_model_manual():
    """Test PRResult model for manual PR creation."""
    result = PRResult(
        status="manual",
        message="Manual PR creation required",
        instructions="Push branch and create PR manually",
    )
    
    assert result.status == "manual"
    assert result.instructions is not None


@pytest.mark.asyncio
async def test_git_platform_is_abstract():
    """Test that GitPlatform cannot be instantiated directly."""
    with pytest.raises(TypeError):
        GitPlatform()


class MockPlatform(GitPlatform):
    """Mock platform for testing abstract methods."""
    
    async def create_pull_request(self, repo, head_branch, base_branch, title, body, draft=False):
        return PRResult(status="success", message="Mock PR created")
    
    async def get_pull_request(self, repo, pr_id):
        return PRInfo(
            id=pr_id,
            title="Mock PR",
            body="",
            state="open",
            head_branch="feature",
            base_branch="main",
            url="https://example.com",
        )
    
    async def list_pull_requests(self, repo, state="open", limit=30):
        return []
    
    async def add_pr_comment(self, repo, pr_id, body):
        pass
    
    @classmethod
    def detect_from_url(cls, remote_url):
        return "mock.example.com" in remote_url
    
    def get_platform_name(self):
        return "Mock Platform"


@pytest.mark.asyncio
async def test_mock_platform_implementation():
    """Test that MockPlatform implements all required methods."""
    platform = MockPlatform()
    
    # Test create_pull_request
    result = await platform.create_pull_request(
        "test/repo",
        "feature",
        "main",
        "Test PR",
        "Description",
    )
    assert result.status == "success"
    
    # Test get_pull_request
    pr = await platform.get_pull_request("test/repo", "123")
    assert pr.id == "123"
    
    # Test list_pull_requests
    prs = await platform.list_pull_requests("test/repo")
    assert isinstance(prs, list)
    
    # Test add_pr_comment
    await platform.add_pr_comment("test/repo", "123", "Test comment")
    
    # Test detect_from_url
    assert MockPlatform.detect_from_url("git@mock.example.com:test/repo.git")
    assert not MockPlatform.detect_from_url("git@github.com:test/repo.git")
    
    # Test get_platform_name
    assert platform.get_platform_name() == "Mock Platform"
