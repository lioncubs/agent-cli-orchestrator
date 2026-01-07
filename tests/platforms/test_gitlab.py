"""Tests for GitLab platform integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.integrations.platforms.gitlab import GitLab


class TestGitLab:
    """Tests for GitLab integration."""
    
    def test_initialization_cloud(self):
        """Test GitLab cloud initialization."""
        platform = GitLab(token="test-token")
        assert platform.base_url == "https://gitlab.com"
        assert platform.token == "test-token"
        assert platform.api_base == "https://gitlab.com/api/v4"
    
    def test_initialization_self_hosted(self):
        """Test GitLab self-hosted initialization."""
        platform = GitLab(base_url="https://gitlab.company.com", token="test-token")
        assert platform.base_url == "https://gitlab.company.com"
        assert platform.api_base == "https://gitlab.company.com/api/v4"
    
    def test_get_platform_name_cloud(self):
        """Test platform name for cloud."""
        platform = GitLab()
        assert platform.get_platform_name() == "GitLab"
    
    def test_get_platform_name_self_hosted(self):
        """Test platform name for self-hosted."""
        platform = GitLab(base_url="https://gitlab.company.com")
        assert platform.get_platform_name() == "GitLab (self-hosted)"
    
    def test_detect_from_url(self):
        """Test URL detection."""
        assert GitLab.detect_from_url("git@gitlab.com:user/repo.git")
        assert GitLab.detect_from_url("https://gitlab.com/user/repo.git")
        assert not GitLab.detect_from_url("git@github.com:user/repo.git")
    
    @pytest.mark.asyncio
    async def test_create_merge_request_no_token(self):
        """Test MR creation without token."""
        platform = GitLab()
        
        result = await platform.create_pull_request(
            "namespace/project",
            "feature-branch",
            "main",
            "Test MR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "token not configured" in result.message.lower()
        assert result.instructions is not None
    
    @pytest.mark.asyncio
    async def test_create_merge_request_success(self):
        """Test successful MR creation."""
        platform = GitLab(token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "iid": 123,
            "web_url": "https://gitlab.com/namespace/project/-/merge_requests/123",
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await platform.create_pull_request(
                "namespace/project",
                "feature-branch",
                "main",
                "Test MR",
                "Test description",
            )
        
        assert result.status == "success"
        assert result.pr_id == "123"
        assert result.pr_number == 123
        assert "gitlab.com" in result.pr_url
    
    @pytest.mark.asyncio
    async def test_create_merge_request_draft(self):
        """Test creating draft MR."""
        platform = GitLab(token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "iid": 124,
            "web_url": "https://gitlab.com/namespace/project/-/merge_requests/124",
        }
        mock_response.raise_for_status = MagicMock()
        
        posted_payload = {}
        
        async def capture_post(url, json=None, headers=None):
            nonlocal posted_payload
            posted_payload = json
            return mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=capture_post
            )
            
            result = await platform.create_pull_request(
                "namespace/project",
                "feature-branch",
                "main",
                "Test MR",
                "Test description",
                draft=True,
            )
        
        assert result.status == "success"
        assert posted_payload["title"].startswith("Draft:")
    
    @pytest.mark.asyncio
    async def test_get_merge_request(self):
        """Test getting MR details."""
        platform = GitLab(token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "iid": 123,
            "title": "Test MR",
            "description": "Test description",
            "state": "opened",
            "source_branch": "feature",
            "target_branch": "main",
            "web_url": "https://gitlab.com/namespace/project/-/merge_requests/123",
            "author": {"username": "testuser"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "merged_at": None,
            "draft": False,
            "work_in_progress": False,
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            mr = await platform.get_pull_request("namespace/project", "123")
        
        assert mr.id == "123"
        assert mr.number == 123
        assert mr.title == "Test MR"
        assert mr.state == "opened"
        assert mr.head_branch == "feature"
        assert mr.base_branch == "main"
        assert not mr.draft
    
    @pytest.mark.asyncio
    async def test_list_merge_requests(self):
        """Test listing MRs."""
        platform = GitLab(token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "iid": 123,
                "title": "MR 1",
                "description": "Desc 1",
                "state": "opened",
                "source_branch": "feature1",
                "target_branch": "main",
                "web_url": "https://gitlab.com/namespace/project/-/merge_requests/123",
                "author": {"username": "user1"},
                "draft": False,
                "work_in_progress": False,
            },
            {
                "iid": 124,
                "title": "MR 2",
                "description": "Desc 2",
                "state": "merged",
                "source_branch": "feature2",
                "target_branch": "main",
                "web_url": "https://gitlab.com/namespace/project/-/merge_requests/124",
                "author": {"username": "user2"},
                "draft": False,
                "work_in_progress": False,
            },
        ]
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            mrs = await platform.list_pull_requests("namespace/project", state="open", limit=10)
        
        assert len(mrs) == 2
        assert mrs[0].id == "123"
        assert mrs[1].id == "124"
    
    @pytest.mark.asyncio
    async def test_add_mr_note(self):
        """Test adding MR note."""
        platform = GitLab(token="test-token")
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await platform.add_pr_comment("namespace/project", "123", "Test note")
        
        # Should not raise exception
