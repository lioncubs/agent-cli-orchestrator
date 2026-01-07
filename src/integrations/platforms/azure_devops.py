"""Azure DevOps (Services and Server) platform integration."""

import httpx
from typing import List, Optional
from .base import GitPlatform, PRResult, PRInfo


class AzureDevOps(GitPlatform):
    """Azure DevOps (cloud and server) integration."""
    
    def __init__(
        self,
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize Azure DevOps integration.
        
        Args:
            organization: Azure DevOps organization name (for cloud)
            base_url: Base URL for Azure DevOps Server (on-premises)
            token: Personal access token
        """
        self.organization = organization
        self.token = token
        
        if base_url:
            # Azure DevOps Server (on-premises)
            self.base_url = base_url.rstrip("/")
            self.is_cloud = False
        else:
            # Azure DevOps Services (cloud)
            self.base_url = "https://dev.azure.com"
            self.is_cloud = True
        
        self.api_version = "7.0"
    
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
        Create a pull request on Azure DevOps.
        
        Args:
            repo: Repository in format "project/repository"
            head_branch: Source branch name
            base_branch: Target branch name
            title: PR title
            body: PR description
            draft: Whether to create as draft PR
            
        Returns:
            PRResult: Result of PR creation
        """
        if not self.token:
            return PRResult(
                status="error",
                message="Azure DevOps token not configured",
                error="Missing personal access token",
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        
        if not self.organization and self.is_cloud:
            return PRResult(
                status="error",
                message="Azure DevOps organization not configured",
                error="Missing organization name",
                instructions=self._get_manual_pr_instructions(repo, head_branch, base_branch, title),
            )
        
        try:
            # Parse repo as "project/repository"
            parts = repo.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid repo format: {repo}. Expected 'project/repository'")
            project, repository = parts
            
            async with httpx.AsyncClient() as client:
                if self.is_cloud:
                    url = f"{self.base_url}/{self.organization}/{project}/_apis/git/repositories/{repository}/pullrequests"
                else:
                    url = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullrequests"
                
                payload = {
                    "sourceRefName": f"refs/heads/{head_branch}",
                    "targetRefName": f"refs/heads/{base_branch}",
                    "title": title,
                    "description": body,
                    "isDraft": draft,
                }
                
                # Azure DevOps uses Basic auth with PAT
                import base64
                auth_value = base64.b64encode(f":{self.token}".encode()).decode()
                
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Basic {auth_value}",
                        "Content-Type": "application/json",
                    },
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                
                data = response.json()
                pr_id = str(data.get("pullRequestId"))
                
                if self.is_cloud:
                    pr_url = f"{self.base_url}/{self.organization}/{project}/_git/{repository}/pullrequest/{pr_id}"
                else:
                    pr_url = f"{self.base_url}/{project}/_git/{repository}/pullrequest/{pr_id}"
                
                return PRResult(
                    status="success",
                    pr_id=pr_id,
                    pr_number=data.get("pullRequestId"),
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
        """Get Azure DevOps pull request details."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            if self.is_cloud:
                url = f"{self.base_url}/{self.organization}/{project}/_apis/git/repositories/{repository}/pullrequests/{pr_id}"
            else:
                url = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullrequests/{pr_id}"
            
            import base64
            auth_value = base64.b64encode(f":{self.token}".encode()).decode()
            
            response = await client.get(
                url,
                headers={"Authorization": f"Basic {auth_value}"},
                params={"api-version": self.api_version},
            )
            response.raise_for_status()
            data = response.json()
            
            # Azure DevOps states: active, completed, abandoned
            state = data.get("status", "").lower()
            if state == "completed":
                state = "merged" if data.get("mergeStatus") == "succeeded" else "closed"
            elif state == "active":
                state = "open"
            
            if self.is_cloud:
                pr_url = f"{self.base_url}/{self.organization}/{project}/_git/{repository}/pullrequest/{pr_id}"
            else:
                pr_url = f"{self.base_url}/{project}/_git/{repository}/pullrequest/{pr_id}"
            
            return PRInfo(
                id=str(data.get("pullRequestId")),
                number=data.get("pullRequestId"),
                title=data.get("title", ""),
                body=data.get("description", ""),
                state=state,
                head_branch=data.get("sourceRefName", "").replace("refs/heads/", ""),
                base_branch=data.get("targetRefName", "").replace("refs/heads/", ""),
                url=pr_url,
                author=data.get("createdBy", {}).get("displayName"),
                created_at=data.get("creationDate"),
                draft=data.get("isDraft", False),
            )
    
    async def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 30,
    ) -> List[PRInfo]:
        """List Azure DevOps pull requests."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            if self.is_cloud:
                url = f"{self.base_url}/{self.organization}/{project}/_apis/git/repositories/{repository}/pullrequests"
            else:
                url = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullrequests"
            
            # Azure DevOps status: active, completed, abandoned, all
            ado_status = "all"
            if state == "open":
                ado_status = "active"
            elif state == "closed":
                ado_status = "completed"
            elif state == "merged":
                ado_status = "completed"
            
            import base64
            auth_value = base64.b64encode(f":{self.token}".encode()).decode()
            
            response = await client.get(
                url,
                headers={"Authorization": f"Basic {auth_value}"},
                params={
                    "api-version": self.api_version,
                    "searchCriteria.status": ado_status,
                    "$top": min(limit, 100),
                },
            )
            response.raise_for_status()
            data = response.json()
            
            prs = []
            for item in data.get("value", [])[:limit]:
                pr_id = item.get("pullRequestId")
                
                # Convert state
                item_state = item.get("status", "").lower()
                if item_state == "completed":
                    item_state = "merged" if item.get("mergeStatus") == "succeeded" else "closed"
                elif item_state == "active":
                    item_state = "open"
                
                if self.is_cloud:
                    pr_url = f"{self.base_url}/{self.organization}/{project}/_git/{repository}/pullrequest/{pr_id}"
                else:
                    pr_url = f"{self.base_url}/{project}/_git/{repository}/pullrequest/{pr_id}"
                
                prs.append(PRInfo(
                    id=str(pr_id),
                    number=pr_id,
                    title=item.get("title", ""),
                    body=item.get("description", ""),
                    state=item_state,
                    head_branch=item.get("sourceRefName", "").replace("refs/heads/", ""),
                    base_branch=item.get("targetRefName", "").replace("refs/heads/", ""),
                    url=pr_url,
                    author=item.get("createdBy", {}).get("displayName"),
                    created_at=item.get("creationDate"),
                    draft=item.get("isDraft", False),
                ))
            
            return prs
    
    async def add_pr_comment(self, repo: str, pr_id: str, body: str) -> None:
        """Add comment to Azure DevOps pull request."""
        parts = repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}")
        project, repository = parts
        
        async with httpx.AsyncClient() as client:
            if self.is_cloud:
                url = f"{self.base_url}/{self.organization}/{project}/_apis/git/repositories/{repository}/pullrequests/{pr_id}/threads"
            else:
                url = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullrequests/{pr_id}/threads"
            
            payload = {
                "comments": [
                    {
                        "parentCommentId": 0,
                        "content": body,
                        "commentType": 1,  # Text comment
                    }
                ],
                "status": 1,  # Active
            }
            
            import base64
            auth_value = base64.b64encode(f":{self.token}".encode()).decode()
            
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Basic {auth_value}",
                    "Content-Type": "application/json",
                },
                params={"api-version": self.api_version},
            )
            response.raise_for_status()
    
    @classmethod
    def detect_from_url(cls, remote_url: str) -> bool:
        """Check if URL is for Azure DevOps."""
        url_lower = remote_url.lower()
        return "dev.azure.com" in url_lower or "visualstudio.com" in url_lower
    
    def get_platform_name(self) -> str:
        """Get platform name."""
        if self.is_cloud:
            return "Azure DevOps Services"
        return "Azure DevOps Server"
    
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
            if self.is_cloud and self.organization:
                url = f"{self.base_url}/{self.organization}/{project}/_git/{repository}/pullrequestcreate"
            elif not self.is_cloud:
                url = f"{self.base_url}/{project}/_git/{repository}/pullrequestcreate"
            else:
                url = self.base_url
        else:
            url = self.base_url
        
        return f"""
To create a pull request manually:

1. Go to: {url}
2. Select source branch: {head_branch}
3. Select target branch: {base_branch}
4. Set title: {title}
5. Add description and submit

Or use the Azure CLI:
  az repos pr create --source-branch {head_branch} --target-branch {base_branch} --title "{title}"
        """.strip()
