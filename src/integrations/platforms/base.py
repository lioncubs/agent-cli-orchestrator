"""Base abstract class for Git platform integrations."""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class PRInfo(BaseModel):
    """Pull request information."""
    
    id: str
    number: Optional[int] = None
    title: str
    body: str
    state: str  # "open", "closed", "merged"
    head_branch: str
    base_branch: str
    url: str
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    draft: bool = False


class PRResult(BaseModel):
    """Result of creating a pull request."""
    
    status: str  # "success" or "error"
    pr_id: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    message: str
    error: Optional[str] = None
    instructions: Optional[str] = None  # For manual PR creation


class GitPlatform(ABC):
    """Abstract base class for Git platform integrations."""
    
    @abstractmethod
    async def create_pull_request(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
    ) -> PRResult:
        """
        Create a pull request on the platform.
        
        Args:
            repo: Repository identifier (format varies by platform)
            head_branch: Source branch name
            base_branch: Target branch name
            title: PR title
            body: PR description
            draft: Whether to create as draft PR
            
        Returns:
            PRResult: Result of PR creation
        """
        pass
    
    @abstractmethod
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        """
        Get pull request details.
        
        Args:
            repo: Repository identifier
            pr_id: Pull request ID or number
            
        Returns:
            PRInfo: Pull request information
        """
        pass
    
    @abstractmethod
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """
        List pull requests in a repository.
        
        Args:
            repo: Repository identifier
            state: Filter by state ("open", "closed", "merged", "all")
            limit: Maximum number of PRs to return
            
        Returns:
            List[PRInfo]: List of pull requests
        """
        pass
    
    @abstractmethod
    async def add_pr_comment(
        self,
        repo: str,
        pr_id: str,
        body: str,
    ) -> None:
        """
        Add a comment to a pull request.
        
        Args:
            repo: Repository identifier
            pr_id: Pull request ID or number
            body: Comment text
        """
        pass
    
    @classmethod
    @abstractmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """
        Check if this platform handles the given remote URL.
        
        Args:
            remote_url: Git remote URL
            
        Returns:
            bool: True if this platform can handle the URL
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            str: Platform name (e.g., "Bitbucket Cloud", "GitLab")
        """
        pass
