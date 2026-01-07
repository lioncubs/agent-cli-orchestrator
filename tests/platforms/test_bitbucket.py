"""Tests for Bitbucket platform integrations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.integrations.platforms.bitbucket import BitbucketCloud, BitbucketServer


class TestBitbucketCloud:
    """Tests for Bitbucket Cloud integration."""
    
    def test_initialization(self):
        """Test BitbucketCloud initialization."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        assert platform.username == "testuser"
        assert platform.app_password == "testpass"
        assert platform.base_url == "https://api.bitbucket.org/2.0"
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = BitbucketCloud()
        assert platform.get_platform_name() == "Bitbucket Cloud"
    
    def test_detect_from_url(self):
        """Test URL detection."""
        assert BitbucketCloud.detect_from_url("git@bitbucket.org:user/repo.git")
        assert BitbucketCloud.detect_from_url("https://bitbucket.org/user/repo.git")
        assert not BitbucketCloud.detect_from_url("git@github.com:user/repo.git")
    
    @pytest.mark.asyncio
    async def test_create_pull_request_no_credentials(self):
        """Test PR creation without credentials."""
        platform = BitbucketCloud()
        
        result = await platform.create_pull_request(
            "workspace/repo",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "credentials not configured" in result.message.lower()
        assert result.instructions is not None
    
    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful PR creation."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "links": {"html": {"href": "https://bitbucket.org/workspace/repo/pull-requests/123"}},
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await platform.create_pull_request(
                "workspace/repo",
                "feature-branch",
                "main",
                "Test PR",
                "Test description",
            )
        
        assert result.status == "success"
        assert result.pr_id == "123"
        assert result.pr_number == 123
        assert "bitbucket.org" in result.pr_url
    
    @pytest.mark.asyncio
    async def test_create_pull_request_http_error(self):
        """Test PR creation with HTTP error."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock()
            mock_post.side_effect = Exception("Network error")
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            result = await platform.create_pull_request(
                "workspace/repo",
                "feature-branch",
                "main",
                "Test PR",
                "Test description",
            )
        
        assert result.status == "error"
        assert "Failed to create pull request" in result.message
        assert result.instructions is not None
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self):
        """Test getting PR details."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "title": "Test PR",
            "description": "Test description",
            "state": "OPEN",
            "source": {"branch": {"name": "feature"}},
            "destination": {"branch": {"name": "main"}},
            "links": {"html": {"href": "https://bitbucket.org/workspace/repo/pull-requests/123"}},
            "author": {"display_name": "Test User"},
            "created_on": "2024-01-01T00:00:00Z",
            "updated_on": "2024-01-02T00:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            pr = await platform.get_pull_request("workspace/repo", "123")
        
        assert pr.id == "123"
        assert pr.number == 123
        assert pr.title == "Test PR"
        assert pr.state == "open"
        assert pr.head_branch == "feature"
        assert pr.base_branch == "main"
    
    @pytest.mark.asyncio
    async def test_list_pull_requests(self):
        """Test listing PRs."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [
                {
                    "id": 123,
                    "title": "PR 1",
                    "description": "Desc 1",
                    "state": "OPEN",
                    "source": {"branch": {"name": "feature1"}},
                    "destination": {"branch": {"name": "main"}},
                    "links": {"html": {"href": "https://bitbucket.org/workspace/repo/pull-requests/123"}},
                    "author": {"display_name": "User 1"},
                },
                {
                    "id": 124,
                    "title": "PR 2",
                    "description": "Desc 2",
                    "state": "MERGED",
                    "source": {"branch": {"name": "feature2"}},
                    "destination": {"branch": {"name": "main"}},
                    "links": {"html": {"href": "https://bitbucket.org/workspace/repo/pull-requests/124"}},
                    "author": {"display_name": "User 2"},
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            prs = await platform.list_pull_requests("workspace/repo", state="open", limit=10)
        
        assert len(prs) == 2
        assert prs[0].id == "123"
        assert prs[1].id == "124"
    
    @pytest.mark.asyncio
    async def test_add_pr_comment(self):
        """Test adding PR comment."""
        platform = BitbucketCloud(username="testuser", app_password="testpass")
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await platform.add_pr_comment("workspace/repo", "123", "Test comment")
        
        # Should not raise exception


class TestBitbucketServer:
    """Tests for Bitbucket Server integration."""
    
    def test_initialization(self):
        """Test BitbucketServer initialization."""
        platform = BitbucketServer(
            base_url="https://bitbucket.company.com",
            username="testuser",
            token="testtoken",
        )
        assert platform.base_url == "https://bitbucket.company.com"
        assert platform.username == "testuser"
        assert platform.token == "testtoken"
        assert platform.api_base == "https://bitbucket.company.com/rest/api/1.0"
    
    def test_get_platform_name(self):
        """Test platform name."""
        platform = BitbucketServer(base_url="https://bitbucket.company.com")
        assert platform.get_platform_name() == "Bitbucket Server"
    
    def test_detect_from_url(self):
        """Test URL detection (always False for self-hosted)."""
        assert not BitbucketServer.detect_from_url("https://bitbucket.company.com/repo.git")
    
    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful PR creation on Bitbucket Server."""
        platform = BitbucketServer(
            base_url="https://bitbucket.company.com",
            username="testuser",
            token="testtoken",
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 456,
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await platform.create_pull_request(
                "PROJECT/repository",
                "feature-branch",
                "main",
                "Test PR",
                "Test description",
            )
        
        assert result.status == "success"
        assert result.pr_id == "456"
        assert "bitbucket.company.com" in result.pr_url
    
    @pytest.mark.asyncio
    async def test_create_pull_request_invalid_repo_format(self):
        """Test PR creation with invalid repo format."""
        platform = BitbucketServer(
            base_url="https://bitbucket.company.com",
            username="testuser",
            token="testtoken",
        )
        
        result = await platform.create_pull_request(
            "invalid-repo-format",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "Invalid repo format" in result.error
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self):
        """Test getting PR details from Bitbucket Server."""
        platform = BitbucketServer(
            base_url="https://bitbucket.company.com",
            username="testuser",
            token="testtoken",
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 456,
            "title": "Test PR",
            "description": "Test description",
            "state": "OPEN",
            "fromRef": {"displayId": "feature"},
            "toRef": {"displayId": "main"},
            "author": {"user": {"displayName": "Test User"}},
            "createdDate": 1640995200000,
            "updatedDate": 1641081600000,
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            pr = await platform.get_pull_request("PROJECT/repository", "456")
        
        assert pr.id == "456"
        assert pr.number == 456
        assert pr.title == "Test PR"
        assert pr.state == "open"
