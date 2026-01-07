"""Bitbucket Cloud and Server platform integrations."""

import httpx
from typing import List, Optional
from .base import GitPlatform, PRResult, PRInfo


class BitbucketCloud(GitPlatform):
    """Bitbucket Cloud (bitbucket.org) integration."""
    
    def __init__(
        self,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
    ):
        """
        Initialize Bitbucket Cloud integration.
        
        Args:
            username: Bitbucket username
            app_password: Bitbucket app password (NOT regular password)
        """
        self.username = username
        self.app_password = app_password
        self.base_url = "https://api.bitbucket.org/2.0"
    
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
        Create a pull request on Bitbucket Cloud.
        
        Args:
            repo: Repository in format "workspace/repo_slug"
            head_branch: Source branch name
            base_branch: Target branch name
            title: PR title
            body: PR description
            draft: Whether to create as draft PR (not supported by Bitbucket)
            
        Returns:
            PRResult: Result of PR creation
        """
        if not self.username or not self.app_password:
            return PRResult(
                status="error",
                message="Bitbucket credentials not configured",
                error="Missing username or app_password",
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/repositories/{repo}/pullrequests"
                payload = {
                    "title": title,
                    "description": body,
                    "source": {
                        "branch": {
                            "name": head_branch
                        }
                    },
                    "destination": {
                        "branch": {
                            "name": base_branch
                        }
                    },
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    auth=(self.username, self.app_password),
                )
                response.raise_for_status()
                
                data = response.json()
                pr_id = str(data.get("id"))
                pr_url = data.get("links", {}).get("html", {}).get("href", "")
                
                return PRResult(
                    status="success",
                    pr_id=pr_id,
                    pr_number=data.get("id"),
                    pr_url=pr_url,
                    message=f"Pull request created successfully: {pr_url}",
                )
        
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            return PRResult(
                status="error",
                message=f"Failed to create pull request: {e}",
                error=error_detail,
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        except Exception as e:
            return PRResult(
                status="error",
                message=f"Failed to create pull request: {str(e)}",
                error=str(e),
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
    
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        """Get Bitbucket pull request details."""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}"
            response = await client.get(
                url,
                auth=(self.username, self.app_password) if self.username and self.app_password else None,
            )
            response.raise_for_status()
            data = response.json()
            
            return PRInfo(
                id=str(data.get("id")),
                number=data.get("id"),
                title=data.get("title", ""),
                body=data.get("description", ""),
                state=data.get("state", "").lower(),
                head_branch=data.get("source", {}).get("branch", {}).get("name", ""),
                base_branch=data.get("destination", {}).get("branch", {}).get("name", ""),
                url=data.get("links", {}).get("html", {}).get("href", ""),
                author=data.get("author", {}).get("display_name"),
                created_at=data.get("created_on"),
                updated_at=data.get("updated_on"),
            )
    
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """List Bitbucket pull requests."""
        async with httpx.AsyncClient() as client:
            # Bitbucket uses OPEN, MERGED, DECLINED
            bb_state = state.upper() if state in ["open", "merged", "declined"] else None
            
            url = f"{self.base_url}/repositories/{repo}/pullrequests"
            params = {"pagelen": min(limit, 50)}
            if bb_state:
                params["state"] = bb_state
            
            response = await client.get(
                url,
                params=params,
                auth=(self.username, self.app_password) if self.username and self.app_password else None,
            )
            response.raise_for_status()
            data = response.json()
            
            prs = []
            for item in data.get("values", [])[:limit]:
                prs.append(PRInfo(
                    id=str(item.get("id")),
                    number=item.get("id"),
                    title=item.get("title", ""),
                    body=item.get("description", ""),
                    state=item.get("state", "").lower(),
                    head_branch=item.get("source", {}).get("branch", {}).get("name", ""),
                    base_branch=item.get("destination", {}).get("branch", {}).get("name", ""),
                    url=item.get("links", {}).get("html", {}).get("href", ""),
                    author=item.get("author", {}).get("display_name"),
                    created_at=item.get("created_on"),
                    updated_at=item.get("updated_on"),
                ))
            
            return prs
    
    async def add_pr_comment(self, repo: str, pr_id: str, body: str) -> None:
        """Add comment to Bitbucket pull request."""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}/comments"
            payload = {"content": {"raw": body}}
            
            response = await client.post(
                url,
                json=payload,
                auth=(self.username, self.app_password),
            )
            response.raise_for_status()
    
    @classmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Check if URL is for Bitbucket Cloud."""
        return "bitbucket.org" in remote_url.lower()
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "Bitbucket Cloud"
    
    def _get_manual_pr_instructions(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
    ) -> str:
        """Get manual PR creation instructions."""
        return f"""
To create a pull request manually:

1. Go to: https://bitbucket.org/{repo}/pull-requests/new
2. Select source branch: {head_branch}
3. Select destination branch: {base_branch}
4. Set title: {title}
5. Add description and submit

Or push your branch and use the Bitbucket UI to create the PR.
        """.strip()


class BitbucketServer(GitPlatform):
    """Bitbucket Server (self-hosted) integration."""
    
    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize Bitbucket Server integration.
        
        Args:
            base_url: Base URL of Bitbucket Server (e.g., https://bitbucket.company.com)
            username: Bitbucket username
            token: Personal access token
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.token = token
        self.api_base = f"{self.base_url}/rest/api/1.0"
    
    async def create_pull_request(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
    ) -> PRResult:
        """Create pull request on Bitbucket Server."""
        if not self.username or not self.token:
            return PRResult(
                status="error",
                message="Bitbucket Server credentials not configured",
                error="Missing username or token",
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        
        try:
            # Parse repo as "project/repository"
            parts = repo.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid repo format: {repo}. Expected 'project/repository'")
            project, repository = parts
            
            async with httpx.AsyncClient() as client:
                url = f"{self.api_base}/projects/{project}/repos/{repository}/pull-requests"
                payload = {
                    "title": title,
                    "description": body,
                    "fromRef": {
                        "id": f"refs/heads/{head_branch}",
                        "repository": {
                            "slug": repository,
                            "project": {"key": project}
                        }
                    },
                    "toRef": {
                        "id": f"refs/heads/{base_branch}",
                        "repository": {
                            "slug": repository,
                            "project": {"key": project}
                        }
                    },
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    auth=(self.username, self.token),
                )
                response.raise_for_status()
                
                data = response.json()
                pr_id = str(data.get("id"))
                pr_url = f"{self.base_url}/projects/{project}/repos/{repository}/pull-requests/{pr_id}"
                
                return PRResult(
                    status="success",
                    pr_id=pr_id,
                    pr_number=data.get("id"),
                    pr_url=pr_url,
                    message=f"Pull request created successfully: {pr_url}",
                )
        
        except Exception as e:
            return PRResult(
                status="error",
                message=f"Failed to create pull request: {str(e)}",
                error=str(e),
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
    
    async def get_pull_request(self, repo: str, pr_id: str) -> PRInfo:
        """Get Bitbucket Server pull request details."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/projects/{project}/repos/{repository}/pull-requests/{pr_id}"
            response = await client.get(
                url,
                auth=(self.username, self.token) if self.username and self.token else None,
            )
            response.raise_for_status()
            data = response.json()
            
            return PRInfo(
                id=str(data.get("id")),
                number=data.get("id"),
                title=data.get("title", ""),
                body=data.get("description", ""),
                state=data.get("state", "").lower(),
                head_branch=data.get("fromRef", {}).get("displayId", ""),
                base_branch=data.get("toRef", {}).get("displayId", ""),
                url=f"{self.base_url}/projects/{project}/repos/{repository}/pull-requests/{pr_id}",
                author=data.get("author", {}).get("user", {}).get("displayName"),
                created_at=data.get("createdDate"),
                updated_at=data.get("updatedDate"),
            )
    
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """List Bitbucket Server pull requests."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/projects/{project}/repos/{repository}/pull-requests"
            params = {"limit": min(limit, 100)}
            if state != "all":
                params["state"] = state.upper()
            
            response = await client.get(
                url,
                params=params,
                auth=(self.username, self.token) if self.username and self.token else None,
            )
            response.raise_for_status()
            data = response.json()
            
            prs = []
            for item in data.get("values", [])[:limit]:
                pr_id = item.get("id")
                prs.append(PRInfo(
                    id=str(pr_id),
                    number=pr_id,
                    title=item.get("title", ""),
                    body=item.get("description", ""),
                    state=item.get("state", "").lower(),
                    head_branch=item.get("fromRef", {}).get("displayId", ""),
                    base_branch=item.get("toRef", {}).get("displayId", ""),
                    url=f"{self.base_url}/projects/{project}/repos/{repository}/pull-requests/{pr_id}",
                    author=item.get("author", {}).get("user", {}).get("displayName"),
                    created_at=item.get("createdDate"),
                    updated_at=item.get("updatedDate"),
                ))
            
            return prs
    
    async def add_pr_comment(self, repo: str, pr_id: str, body: str) -> None:
        """Add comment to Bitbucket Server pull request."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            url = f"{self.api_base}/projects/{project}/repos/{repository}/pull-requests/{pr_id}/comments"
            payload = {"text": body}
            
            response = await client.post(
                url,
                json=payload,
                auth=(self.username, self.token),
            )
            response.raise_for_status()
    
    @classmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Check if URL is for Bitbucket Server."""
        # Bitbucket Server is self-hosted, requires configuration
        return False
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        return "Bitbucket Server"
    
    def _get_manual_pr_instructions(
        self,
        repo: str,
        head_branch: str,
        base_branch: str,
        title: str,
    ) -> str:
        """Get manual PR creation instructions."""
        parts = repo.split("/")
        if len(parts) == 2:
            project, repository = parts
            url = f"{self.base_url}/projects/{project}/repos/{repository}/pull-requests"
        else:
            url = f"{self.base_url}"
        
        return f"""
To create a pull request manually:

1. Go to: {url}
2. Click "Create pull request"
3. Select source branch: {head_branch}
4. Select destination branch: {base_branch}
5. Set title: {title}
6. Add description and submit
        """.strip()
