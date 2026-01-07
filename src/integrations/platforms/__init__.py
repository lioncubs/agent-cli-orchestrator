"""
Platform integrations for Git hosting services.

Provides unified interface for creating pull requests across different platforms.
"""

from typing import Optional
from .base import GitPlatform, PRResult, PRInfo
from .bitbucket import BitbucketCloud, BitbucketServer
from .gitlab import GitLab
from .azure_devops import AzureDevOps
from .generic import GenericPlatform

__all__ = [
    "GitPlatform",
    "PRResult",
    "PRInfo",
    "BitbucketCloud",
    "BitbucketServer",
    "GitLab",
    "AzureDevOps",
    "GenericPlatform",
    "detect_platform",
]


def detect_platform(remote_url: str, config: Optional[dict] = None) -> GitPlatform:
    """
    Auto-detect Git platform from remote URL.
    
    Args:
        remote_url: Git remote URL (SSH or HTTPS)
        config: Optional configuration for platform initialization
        
    Returns:
        GitPlatform: Detected platform instance
        
    Examples:
        >>> detect_platform("git@bitbucket.org:user/repo.git")
        <BitbucketCloud ...>
        
        >>> detect_platform("https://gitlab.com/user/repo.git")
        <GitLab ...>
        
        >>> detect_platform("git@ssh.dev.azure.com:v3/org/project/repo")
        <AzureDevOps ...>
    """
    config = config or {}
    
    # Normalize URL for checking
    url_lower = remote_url.lower()
    
    # Bitbucket Cloud
    if "bitbucket.org" in url_lower:
        return BitbucketCloud(
            username=config.get("username"),
            app_password=config.get("app_password"),
        )
    
    # Bitbucket Server (self-hosted)
    if config.get("bitbucket_server_url") and config["bitbucket_server_url"] in remote_url:
        return BitbucketServer(
            base_url=config["bitbucket_server_url"],
            username=config.get("username"),
            token=config.get("token"),
        )
    
    # GitLab (cloud or self-hosted)
    if "gitlab.com" in url_lower or config.get("gitlab_url"):
        base_url = config.get("gitlab_url")
        if not base_url:
            base_url = "https://gitlab.com" if "gitlab.com" in url_lower else None
        return GitLab(
            base_url=base_url,
            token=config.get("token"),
        )
    
    # Azure DevOps
    if "dev.azure.com" in url_lower or "visualstudio.com" in url_lower:
        return AzureDevOps(
            organization=config.get("organization"),
            token=config.get("token"),
        )
    
    # Azure DevOps Server (on-premises)
    if config.get("azure_server_url") and config["azure_server_url"] in remote_url:
        return AzureDevOps(
            base_url=config["azure_server_url"],
            token=config.get("token"),
        )
    
    # Generic fallback for unknown platforms or manual PR creation
    return GenericPlatform(remote_url=remote_url)
