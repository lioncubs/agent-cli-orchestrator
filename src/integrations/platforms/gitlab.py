"""GitLab (Cloud and self-hosted) platform integration."""

import httpx
from typing import List, Optional
from .base import GitPlatform, PRResult, PRInfo


class GitLab(GitPlatform):
    """GitLab (gitlab.com or self-hosted) integration."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize GitLab integration.
        
        Args:
            base_url: Base URL (defaults to https://gitlab.com for cloud)
            token: Personal access token with API scope
        """
        self.base_url = (base_url or "https://gitlab.com").rstrip("/")
        self.token = token
        self.api_base = f"{self.base_url}/api/v4"
    
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
        Create a merge request on GitLab.
        
        Args:
            repo: Project ID or "namespace/project" path
            head_branch: Source branch name
            base_branch: Target branch name
            title: MR title
            body: MR description
            draft: Whether to create as draft MR
            
        Returns:
            PRResult: Result of MR creation
        """
        if not self.token:
            return PRResult(
                status="error",
                message="GitLab token not configured",
                error="Missing personal access token",
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        
        try:
            # URL encode the repo path
            import urllib.parse
            encoded_repo = urllib.parse.quote(repo, safe='')
            
            async with httpx.AsyncClient() as client:
                url = f"{self.api_base}/projects/{encoded_repo}/merge_requests"
                
                # GitLab uses title prefix for draft
                mr_title = title
                if draft:
                    if not title.startswith("Draft:") and not title.startswith("WIP:"):
                        mr_title = f"Draft: {title}"
                
                payload = {
                    "source_branch": head_branch,
                    "target_branch": base_branch,
                    "title": mr_title,
                    "description": body,
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    headers={"PRIVATE-TOKEN": self.token},
                )
                response.raise_for_status()
                
                data = response.json()
                mr_id = str(data.get("iid"))  # Use internal ID
                mr_url = data.get("web_url", "")
                
                return PRResult(
                    status="success",
                    pr_id=mr_id,
                    pr_number=data.get("iid"),
                    pr_url=mr_url,
                    message=f"Merge request created successfully: {mr_url}",
                )
        
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            return PRResult(
                status="error",
                message=f"Failed to create merge request: {e}",
                error=error_detail,
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        except Exception as e:
            return PRResult(
                status="error",
                message=f"Failed to create merge request: {str(e)}",
                error=str(e),
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
    
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        """Get GitLab merge request details."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(repo, safe='')
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/projects/{encoded_repo}/merge_requests/{pr_id}"
            headers = {}
            if self.token:
                headers["PRIVATE-TOKEN"] = self.token
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return PRInfo(
                id=str(data.get("iid")),
                number=data.get("iid"),
                title=data.get("title", ""),
                body=data.get("description", ""),
                state=data.get("state", "").lower(),
                head_branch=data.get("source_branch", ""),
                base_branch=data.get("target_branch", ""),
                url=data.get("web_url", ""),
                author=data.get("author", {}).get("username"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                merged_at=data.get("merged_at"),
                draft=data.get("draft", False) or data.get("work_in_progress", False),
            )
    
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """List GitLab merge requests."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(repo, safe='')
        
        async with httpx.AsyncClient() as client:
            # GitLab uses opened, closed, merged, all
            gl_state = state if state in ["opened", "closed", "merged", "all"] else "opened"
            if state == "open":
                gl_state = "opened"
            
            url = f"{self.api_base}/projects/{encoded_repo}/merge_requests"
            params = {
                "state": gl_state,
                "per_page": min(limit, 100),
            }
            
            headers = {}
            if self.token:
                headers["PRIVATE-TOKEN"] = self.token
            
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            prs = []
            for item in data[:limit]:
                prs.append(PRInfo(
                    id=str(item.get("iid")),
                    number=item.get("iid"),
                    title=item.get("title", ""),
                    body=item.get("description", ""),
                    state=item.get("state", "").lower(),
                    head_branch=item.get("source_branch", ""),
                    base_branch=item.get("target_branch", ""),
                    url=item.get("web_url", ""),
                    author=item.get("author", {}).get("username"),
                    created_at=item.get("created_at"),
                    updated_at=item.get("updated_at"),
                    merged_at=item.get("merged_at"),
                    draft=item.get("draft", False) or item.get("work_in_progress", False),
                ))
            
            return prs
    
    async def add_pr_comment(self, repo: str, pr_id: str, body: str) -> None:
        """Add note to GitLab merge request."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(repo, safe='')
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/projects/{encoded_repo}/merge_requests/{pr_id}/notes"
            payload = {"body": body}
            
            response = await client.post(
                url,
                json=payload,
                headers={"PRIVATE-TOKEN": self.token},
            )
            response.raise_for_status()
    
    @classmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Check if URL is for GitLab."""
        return "gitlab.com" in remote_url.lower()
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        if self.base_url.lower() == "https://gitlab.com":
            return "GitLab"
        return "GitLab (self-hosted)"
    
    def _get_manual_pr_instructions(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
    ) -> str:
        """Get manual MR creation instructions."""
        # Try to construct URL
        if "/" in repo:
            mr_url = f"{self.base_url}/{repo}/-/merge_requests/new"
        else:
            mr_url = f"{self.base_url}"
        
        return f"""
To create a merge request manually:

1. Go to: {mr_url}
2. Select source branch: {head_branch}
3. Select target branch: {base_branch}
4. Set title: {title}
5. Add description and submit

Or use the GitLab CLI:
  glab mr create --source-branch {head_branch} --target-branch {base_branch} --title "{title}"
        """.strip()
