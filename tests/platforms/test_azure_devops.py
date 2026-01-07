"""Tests for Azure DevOps platform integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.integrations.platforms.azure_devops import AzureDevOps


class TestAzureDevOps:
    """Tests for Azure DevOps integration."""
    
    def test_initialization_cloud(self):
        """Test Azure DevOps cloud initialization."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        assert platform.organization == "myorg"
        assert platform.token == "test-token"
        assert platform.base_url == "https://dev.azure.com"
        assert platform.is_cloud is True
    
    def test_initialization_server(self):
        """Test Azure DevOps Server initialization."""
        platform = AzureDevOps(
            base_url="https://azure.company.com",
            token="test-token"
        )
        assert platform.base_url == "https://azure.company.com"
        assert platform.is_cloud is False
    
    def test_get_platform_name_cloud(self):
        """Test platform name for cloud."""
        platform = AzureDevOps(organization="myorg")
        assert platform.get_platform_name() == "Azure DevOps Services"
    
    def test_get_platform_name_server(self):
        """Test platform name for server."""
        platform = AzureDevOps(base_url="https://azure.company.com")
        assert platform.get_platform_name() == "Azure DevOps Server"
    
    def test_detect_from_url(self):
        """Test URL detection."""
        assert AzureDevOps.detect_from_url("git@ssh.dev.azure.com:v3/org/project/repo")
        assert AzureDevOps.detect_from_url("https://dev.azure.com/org/project/_git/repo")
        assert AzureDevOps.detect_from_url("https://org.visualstudio.com/project/_git/repo")
        assert not AzureDevOps.detect_from_url("git@github.com:user/repo.git")
    
    @pytest.mark.asyncio
    async def test_create_pull_request_no_token(self):
        """Test PR creation without token."""
        platform = AzureDevOps(organization="myorg")
        
        result = await platform.create_pull_request(
            "project/repository",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "token not configured" in result.message.lower()
        assert result.instructions is not None
    
    @pytest.mark.asyncio
    async def test_create_pull_request_no_organization(self):
        """Test PR creation without organization (cloud)."""
        platform = AzureDevOps(token="test-token")
        
        result = await platform.create_pull_request(
            "project/repository",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "organization not configured" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_create_pull_request_success_cloud(self):
        """Test successful PR creation on cloud."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pullRequestId": 456,
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await platform.create_pull_request(
                "project/repository",
                "feature-branch",
                "main",
                "Test PR",
                "Test description",
            )
        
        assert result.status == "success"
        assert result.pr_id == "456"
        assert result.pr_number == 456
        assert "dev.azure.com" in result.pr_url
    
    @pytest.mark.asyncio
    async def test_create_pull_request_draft(self):
        """Test creating draft PR."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pullRequestId": 457,
        }
        mock_response.raise_for_status = MagicMock()
        
        posted_payload = {}
        
        async def capture_post(url, json=None, headers=None, params=None):
            nonlocal posted_payload
            posted_payload = json
            return mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=capture_post
            )
            
            result = await platform.create_pull_request(
                "project/repository",
                "feature-branch",
                "main",
                "Test PR",
                "Test description",
                draft=True,
            )
        
        assert result.status == "success"
        assert posted_payload["isDraft"] is True
    
    @pytest.mark.asyncio
    async def test_create_pull_request_invalid_repo_format(self):
        """Test PR creation with invalid repo format."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        result = await platform.create_pull_request(
            "invalid-repo",
            "feature-branch",
            "main",
            "Test PR",
            "Test description",
        )
        
        assert result.status == "error"
        assert "Invalid repo format" in result.error
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self):
        """Test getting PR details."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pullRequestId": 456,
            "title": "Test PR",
            "description": "Test description",
            "status": "active",
            "sourceRefName": "refs/heads/feature",
            "targetRefName": "refs/heads/main",
            "createdBy": {"displayName": "Test User"},
            "creationDate": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "mergeStatus": "succeeded",
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            pr = await platform.get_pull_request("project/repository", "456")
        
        assert pr.id == "456"
        assert pr.number == 456
        assert pr.title == "Test PR"
        assert pr.state == "open"
        assert pr.head_branch == "feature"
        assert pr.base_branch == "main"
        assert not pr.draft
    
    @pytest.mark.asyncio
    async def test_get_pull_request_completed_merged(self):
        """Test getting completed/merged PR details."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pullRequestId": 456,
            "title": "Test PR",
            "description": "Test description",
            "status": "completed",
            "sourceRefName": "refs/heads/feature",
            "targetRefName": "refs/heads/main",
            "createdBy": {"displayName": "Test User"},
            "creationDate": "2024-01-01T00:00:00Z",
            "isDraft": False,
            "mergeStatus": "succeeded",
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            pr = await platform.get_pull_request("project/repository", "456")
        
        assert pr.state == "merged"
    
    @pytest.mark.asyncio
    async def test_list_pull_requests(self):
        """Test listing PRs."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "pullRequestId": 456,
                    "title": "PR 1",
                    "description": "Desc 1",
                    "status": "active",
                    "sourceRefName": "refs/heads/feature1",
                    "targetRefName": "refs/heads/main",
                    "createdBy": {"displayName": "User 1"},
                    "creationDate": "2024-01-01T00:00:00Z",
                    "isDraft": False,
                },
                {
                    "pullRequestId": 457,
                    "title": "PR 2",
                    "description": "Desc 2",
                    "status": "completed",
                    "sourceRefName": "refs/heads/feature2",
                    "targetRefName": "refs/heads/main",
                    "createdBy": {"displayName": "User 2"},
                    "creationDate": "2024-01-02T00:00:00Z",
                    "isDraft": False,
                    "mergeStatus": "succeeded",
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            prs = await platform.list_pull_requests("project/repository", state="open", limit=10)
        
        assert len(prs) == 2
        assert prs[0].id == "456"
        assert prs[1].id == "457"
    
    @pytest.mark.asyncio
    async def test_add_pr_comment(self):
        """Test adding PR comment."""
        platform = AzureDevOps(organization="myorg", token="test-token")
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await platform.add_pr_comment("project/repository", "456", "Test comment")
        
        # Should not raise exception
