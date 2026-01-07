"""Generic platform fallback for manual PR creation."""

from typing import List
from .base import GitPlatform, PRResult, PRInfo


class GenericPlatform(GitPlatform):
    """
    Generic fallback platform for unknown Git hosting services.
    
    Provides manual PR creation instructions instead of API integration.
    """
    
    def __init__(self, remote_url: str = ""):
        """
        Initialize generic platform.
        
        Args:
            remote_url: Git remote URL for reference
        """
        self.remote_url = remote_url
    
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
        Return manual PR creation instructions.
        
        Args:
            repo: Repository identifier
            head_branch: Source branch name
            base_branch: Target branch name
            title: PR title
            body: PR description
            draft: Whether to create as draft PR
            
        Returns:
            PRResult: Manual instructions
        """
        instructions = self._get_manual_pr_instructions(
            repo, head_branch, base_branch, title, body, draft
        )
        
        return PRResult(
            status="manual",
            message="Automatic PR creation not supported for this platform",
            instructions=instructions,
        )
    
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        """Not supported for generic platform."""
        raise NotImplementedError(
            "Pull request retrieval not supported for generic platform. "
            "Please use the web interface of your Git hosting service."
        )
    
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """Not supported for generic platform."""
        raise NotImplementedError(
            "Pull request listing not supported for generic platform. "
            "Please use the web interface of your Git hosting service."
        )
    
    async def add_pr_comment(self, repo: str, pr_id: str, body: str) -> None:
        """Not supported for generic platform."""
        raise NotImplementedError(
            "PR comments not supported for generic platform. "
            "Please use the web interface of your Git hosting service."
        )
    
    @classmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Generic platform is the fallback, so always returns False."""
        return False
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "Generic Git Platform"
    
    def _get_manual_pr_instructions(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool,
    ) -> str:
        """Get manual PR creation instructions."""
        draft_note = "\n6. Mark as draft (if supported)" if draft else ""
        
        instructions = f"""
Manual Pull Request Creation Required

Your changes have been committed to branch: {head_branch}

To create a pull request, please follow these steps:

1. Push your branch to the remote repository:
   git push origin {head_branch}

2. Navigate to your Git hosting service web interface

3. Create a new Pull Request with:
   - Source branch: {head_branch}
   - Target branch: {base_branch}
   - Title: {title}

4. Add the following description:
{body}

5. Review and submit the pull request{draft_note}

Repository: {repo}
Remote URL: {self.remote_url}

If your Git hosting service supports command-line PR creation,
you may be able to use tools like:
  - gh (GitHub CLI)
  - glab (GitLab CLI)
  - az repos (Azure DevOps CLI)
  - bb (Bitbucket CLI)

Consult your platform's documentation for details.
        """.strip()
        
        return instructions
