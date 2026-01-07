"""Tests for platform detection."""

import pytest
from src.integrations.platforms import (
    detect_platform,
    BitbucketCloud,
    BitbucketServer,
    GitLab,
    AzureDevOps,
    GenericPlatform,
)


class TestPlatformDetection:
    """Tests for detect_platform function."""
    
    def test_detect_bitbucket_cloud_ssh(self):
        """Test detection of Bitbucket Cloud via SSH URL."""
        platform = detect_platform("git@bitbucket.org:user/repo.git")
        assert isinstance(platform, BitbucketCloud)
    
    def test_detect_bitbucket_cloud_https(self):
        """Test detection of Bitbucket Cloud via HTTPS URL."""
        platform = detect_platform("https://bitbucket.org/user/repo.git")
        assert isinstance(platform, BitbucketCloud)
    
    def test_detect_bitbucket_cloud_with_config(self):
        """Test Bitbucket Cloud detection with credentials."""
        platform = detect_platform(
            "git@bitbucket.org:user/repo.git",
            config={"username": "testuser", "app_password": "testpass"}
        )
        assert isinstance(platform, BitbucketCloud)
        assert platform.username == "testuser"
        assert platform.app_password == "testpass"
    
    def test_detect_bitbucket_server(self):
        """Test detection of Bitbucket Server."""
        platform = detect_platform(
            "https://bitbucket.company.com/scm/project/repo.git",
            config={
                "bitbucket_server_url": "https://bitbucket.company.com",
                "username": "testuser",
                "token": "testtoken",
            }
        )
        assert isinstance(platform, BitbucketServer)
        assert platform.base_url == "https://bitbucket.company.com"
    
    def test_detect_gitlab_cloud_ssh(self):
        """Test detection of GitLab.com via SSH URL."""
        platform = detect_platform("git@gitlab.com:user/repo.git")
        assert isinstance(platform, GitLab)
        assert "gitlab.com" in platform.base_url
    
    def test_detect_gitlab_cloud_https(self):
        """Test detection of GitLab.com via HTTPS URL."""
        platform = detect_platform("https://gitlab.com/user/repo.git")
        assert isinstance(platform, GitLab)
    
    def test_detect_gitlab_self_hosted(self):
        """Test detection of self-hosted GitLab."""
        platform = detect_platform(
            "git@gitlab.company.com:user/repo.git",
            config={"gitlab_url": "https://gitlab.company.com", "token": "testtoken"}
        )
        assert isinstance(platform, GitLab)
        assert platform.base_url == "https://gitlab.company.com"
    
    def test_detect_azure_devops_ssh(self):
        """Test detection of Azure DevOps via SSH URL."""
        platform = detect_platform("git@ssh.dev.azure.com:v3/org/project/repo")
        assert isinstance(platform, AzureDevOps)
        assert platform.is_cloud is True
    
    def test_detect_azure_devops_https(self):
        """Test detection of Azure DevOps via HTTPS URL."""
        platform = detect_platform("https://dev.azure.com/org/project/_git/repo")
        assert isinstance(platform, AzureDevOps)
    
    def test_detect_azure_devops_visualstudio(self):
        """Test detection of Azure DevOps via visualstudio.com URL."""
        platform = detect_platform("https://org.visualstudio.com/project/_git/repo")
        assert isinstance(platform, AzureDevOps)
    
    def test_detect_azure_devops_with_config(self):
        """Test Azure DevOps detection with configuration."""
        platform = detect_platform(
            "https://dev.azure.com/org/project/_git/repo",
            config={"organization": "myorg", "token": "testtoken"}
        )
        assert isinstance(platform, AzureDevOps)
        assert platform.organization == "myorg"
        assert platform.token == "testtoken"
    
    def test_detect_azure_devops_server(self):
        """Test detection of Azure DevOps Server."""
        platform = detect_platform(
            "https://azure.company.com/project/_git/repo",
            config={
                "azure_server_url": "https://azure.company.com",
                "token": "testtoken",
            }
        )
        assert isinstance(platform, AzureDevOps)
        assert platform.is_cloud is False
        assert platform.base_url == "https://azure.company.com"
    
    def test_detect_generic_unknown_platform(self):
        """Test fallback to GenericPlatform for unknown platforms."""
        platform = detect_platform("https://unknown-git-server.com/repo.git")
        assert isinstance(platform, GenericPlatform)
    
    def test_detect_generic_no_config(self):
        """Test GenericPlatform when no config is provided."""
        platform = detect_platform("git@custom.git-server.com:user/repo.git")
        assert isinstance(platform, GenericPlatform)
        assert platform.remote_url == "git@custom.git-server.com:user/repo.git"
    
    def test_detect_with_none_config(self):
        """Test detection with None config (should use default)."""
        platform = detect_platform("git@gitlab.com:user/repo.git", config=None)
        assert isinstance(platform, GitLab)
    
    def test_detect_platform_priority(self):
        """Test that platform detection follows correct priority."""
        # Bitbucket Cloud has priority over generic
        assert isinstance(
            detect_platform("git@bitbucket.org:user/repo.git"),
            BitbucketCloud
        )
        
        # GitLab has priority over generic
        assert isinstance(
            detect_platform("git@gitlab.com:user/repo.git"),
            GitLab
        )
        
        # Azure DevOps has priority over generic
        assert isinstance(
            detect_platform("git@ssh.dev.azure.com:v3/org/project/repo"),
            AzureDevOps
        )
