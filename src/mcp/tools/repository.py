"""Repository management MCP tools."""

from typing import Dict, Any, List

from src.mcp.models import (
    ListReposInput,
    GetRepoInput,
    RepoInfo,
    MCPError
)
from src.session.models import SessionStatus
from config_loader import config
from src.integrations.git import GitOperations
from src.session.store import SessionStore


class RepositoryTools:
    """MCP tools for repository management."""
    
    def __init__(
        self,
        session_store: SessionStore
    ):
        """
        Initialize repository tools.
        
        Args:
            session_store: Session storage
        """
        self.session_store = session_store
    
    async def list_repos(self, input_data: ListReposInput) -> Dict[str, Any]:
        """
        List all configured repositories.
        
        Args:
            input_data: List parameters (currently none)
            
        Returns:
            List of RepoInfo objects
        """
        try:
            repos = []
            
            for repo_config in config.repositories:
                repo_name = repo_config.get("name")
                repo_path = repo_config.get("path")
                
                if not repo_name or not repo_path:
                    continue
                
                try:
                    git_ops = GitOperations(repo_path)
                    current_branch = git_ops.get_current_branch()
                    default_branch = git_ops.get_default_branch()
                    remote_url = git_ops.get_remote_url()
                    has_uncommitted = git_ops.has_uncommitted_changes()
                    
                    # Count active sessions for this repo
                    all_sessions = await self.session_store.list_sessions(repo_name=repo_name)
                    active_sessions = [s for s in all_sessions if s.status in [SessionStatus.ACTIVE, SessionStatus.COMMITTED]]
                    
                    repos.append(
                        RepoInfo(
                            name=repo_name,
                            path=repo_path,
                            current_branch=current_branch,
                            default_branch=default_branch,
                            remote_url=remote_url,
                            has_uncommitted_changes=has_uncommitted,
                            active_sessions_count=len(active_sessions)
                        ).model_dump()
                    )
                except Exception as e:
                    # If we can't get git info, still include the repo with minimal info
                    repos.append(
                        RepoInfo(
                            name=repo_name,
                            path=repo_path,
                            active_sessions_count=0
                        ).model_dump()
                    )
            
            return {
                "repositories": repos,
                "total": len(repos)
            }
            
        except Exception as e:
            return MCPError(
                error="Failed to list repositories",
                details=str(e)
            ).model_dump()
    
    async def get_repo(self, input_data: GetRepoInput) -> Dict[str, Any]:
        """
        Get details of a specific repository.
        
        Args:
            input_data: Repository name
            
        Returns:
            RepoInfo with full details
        """
        try:
            repo_config = None
            for repo in config.repositories:
                if repo.get("name") == input_data.repo_name:
                    repo_config = repo
                    break
            
            if not repo_config:
                return MCPError(
                    error=f"Repository not found: {input_data.repo_name}"
                ).model_dump()
            
            repo_path = repo_config.get("path")
            
            try:
                git_ops = GitOperations(repo_path)
                current_branch = git_ops.get_current_branch()
                default_branch = git_ops.get_default_branch()
                remote_url = git_ops.get_remote_url()
                has_uncommitted = git_ops.has_uncommitted_changes()
                
                # Count active sessions for this repo
                all_sessions = await self.session_store.list_sessions(repo_name=input_data.repo_name)
                active_sessions = [s for s in all_sessions if s.status in [SessionStatus.ACTIVE, SessionStatus.COMMITTED]]
                
                return RepoInfo(
                    name=input_data.repo_name,
                    path=repo_path,
                    current_branch=current_branch,
                    default_branch=default_branch,
                    remote_url=remote_url,
                    has_uncommitted_changes=has_uncommitted,
                    active_sessions_count=len(active_sessions)
                ).model_dump()
                
            except Exception as e:
                return MCPError(
                    error=f"Failed to get repository info: {input_data.repo_name}",
                    details=str(e)
                ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to get repository",
                details=str(e)
            ).model_dump()
