"""Pull request management for delegation workflows."""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from src.integrations.platforms import detect_platform, GitPlatform


class PRManager:
    """
    Manages pull request creation for delegation sessions.
    
    Supports multiple Git platforms via auto-detection and platform-specific APIs.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize PR manager.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self._platform: Optional[GitPlatform] = None
        self._platform_config: Dict[str, Any] = {}
    
    def set_platform_config(self, config: Dict[str, Any]) -> None:
        """
        Set platform configuration for API access.
        
        Args:
            config: Platform-specific configuration (tokens, credentials, etc.)
        """
        self._platform_config = config
        self._platform = None  # Reset platform to trigger re-detection
    
    def _get_remote_url(self) -> str:
        """
        Get the remote URL for the repository.
        
        Returns:
            Remote URL (typically from origin)
        """
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def _detect_platform(self) -> GitPlatform:
        """
        Detect Git platform from remote URL.
        
        Returns:
            GitPlatform instance for the detected platform
        """
        if self._platform is None:
            remote_url = self._get_remote_url()
            self._platform = detect_platform(remote_url, self._platform_config)
        return self._platform
    
    def _run_command(
        self,
        command: list[str],
        cwd: Optional[Path] = None
    ) -> str:
        """
        Run a command and return output.
        
        Args:
            command: Command as list of arguments
            cwd: Working directory for command (defaults to repo_path)
            
        Returns:
            Command stdout as string
            
        Raises:
            RuntimeError: If command fails
        """
        work_dir = cwd or self.repo_path
        try:
            result = subprocess.run(
                command,
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            raise RuntimeError(f"Command failed: {error_msg}") from e
    
    def push_branch(
        self,
        worktree_path: str,
        branch_name: str,
        force: bool = False
    ) -> None:
        """
        Push branch to remote repository.
        
        Args:
            worktree_path: Path to the worktree
            branch_name: Branch name to push
            force: If True, force push
            
        Raises:
            RuntimeError: If push fails
        """
        path = Path(worktree_path)
        
        command = ['git', 'push', 'origin', branch_name]
        if force:
            command.append('--force')
        
        try:
            self._run_command(command, cwd=path)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to push branch: {e}") from e
    
    async def create_pull_request(
        self,
        worktree_path: str,
        branch_name: str,
        base_branch: str,
        title: str,
        body: Optional[str] = None,
        draft: bool = False,
        repo_identifier: Optional[str] = None,
    ) -> dict:
        """
        Create a pull request using platform API.
        
        Args:
            worktree_path: Path to the worktree
            branch_name: Source branch name
            base_branch: Target base branch
            title: PR title
            body: PR description/body
            draft: If True, create as draft PR
            repo_identifier: Repository identifier (format varies by platform)
            
        Returns:
            Dictionary with PR creation result
            
        Raises:
            RuntimeError: If PR creation fails critically
        """
        path = Path(worktree_path)
        
        # First, push the branch to remote
        try:
            self.push_branch(str(path), branch_name)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to push branch before creating PR: {e}") from e
        
        # Detect platform and create PR
        platform = self._detect_platform()
        
        # Get repository identifier if not provided
        if not repo_identifier:
            # Try to extract from remote URL
            remote_url = self._get_remote_url()
            repo_identifier = self._extract_repo_identifier(remote_url, platform)
        
        # Create PR via platform API
        pr_result = await platform.create_pull_request(
            repo=repo_identifier,
            head_branch=branch_name,
            base_branch=base_branch,
            title=title,
            body=body or "",
            draft=draft,
        )
        
        return {
            "status": pr_result.status,
            "pr_url": pr_result.pr_url,
            "pr_id": pr_result.pr_id,
            "pr_number": pr_result.pr_number,
            "message": pr_result.message,
            "error": pr_result.error,
            "instructions": pr_result.instructions,
            "platform": platform.get_platform_name(),
        }
    
    def _extract_repo_identifier(self, remote_url: str, platform: GitPlatform) -> str:
        """
        Extract repository identifier from remote URL.
        
        Args:
            remote_url: Git remote URL
            platform: Detected platform
            
        Returns:
            Repository identifier in platform-specific format
        """
        # Remove .git suffix if present
        url = remote_url
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract path portion
        if '@' in url:
            # SSH URL: git@host:path or git@host:v3/org/project/repo
            parts = url.split(':', 1)
            if len(parts) == 2:
                path = parts[1]
            else:
                path = url
        else:
            # HTTPS URL: https://host/path
            parts = url.split('/', 3)
            if len(parts) >= 4:
                path = '/'.join(parts[3:])
            else:
                path = url
        
        # Clean up the path
        path = path.strip('/')
        
        # For Azure DevOps, extract project/repo from various URL formats
        platform_name = platform.get_platform_name()
        if "Azure DevOps" in platform_name:
            # Handle various Azure DevOps URL formats
            if '/_git/' in path:
                # Format: org/project/_git/repo -> project/repo
                parts = path.split('/_git/')
                if len(parts) == 2:
                    project = parts[0].split('/')[-1]
                    repo = parts[1]
                    return f"{project}/{repo}"
            elif '/v3/' in path or path.startswith('v3/'):
                # SSH format: v3/org/project/repo -> project/repo
                if path.startswith('v3/'):
                    path = path[3:]  # Remove v3/ prefix
                segments = path.split('/')
                if len(segments) >= 3:
                    # org/project/repo -> project/repo
                    return f"{segments[1]}/{segments[2]}"
                elif len(segments) >= 2:
                    return f"{segments[0]}/{segments[1]}"
        
        return path
    
    async def get_pr_details(
        self,
        repo_identifier: str,
        pr_id: str,
    ) -> dict:
        """
        Get details of a pull request.
        
        Args:
            repo_identifier: Repository identifier
            pr_id: Pull request ID or number
            
        Returns:
            Dictionary with PR details
            
        Raises:
            NotImplementedError: If platform doesn't support PR retrieval
        """
        platform = self._detect_platform()
        
        try:
            pr_info = await platform.get_pull_request(repo_identifier, pr_id)
            
            return {
                "id": pr_info.id,
                "number": pr_info.number,
                "title": pr_info.title,
                "body": pr_info.body,
                "state": pr_info.state,
                "head_branch": pr_info.head_branch,
                "base_branch": pr_info.base_branch,
                "url": pr_info.url,
                "author": pr_info.author,
                "created_at": pr_info.created_at,
                "updated_at": pr_info.updated_at,
                "merged_at": pr_info.merged_at,
                "draft": pr_info.draft,
            }
        except NotImplementedError:
            raise NotImplementedError(
                f"PR retrieval not supported for {platform.get_platform_name()}. "
                "Please use the web interface of your Git hosting service to view PR details."
            )
    
    def get_pr_status(self, worktree_path: str, pr_number: int) -> dict:
        """
        Get status of a pull request (legacy GitHub CLI method).
        
        DEPRECATED: Use get_pr_details() instead for platform-agnostic PR status.
        
        Args:
            worktree_path: Path to the worktree
            pr_number: PR number
            
        Returns:
            Dictionary with PR status information
            
        Raises:
            RuntimeError: If getting PR status fails
        """
        path = Path(worktree_path)
        
        try:
            # Get PR details in JSON format
            output = self._run_command([
                'gh', 'pr', 'view', str(pr_number),
                '--json', 'state,title,url,number,headRefName,baseRefName'
            ], cwd=path)
            
            import json
            return json.loads(output)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to get PR status: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse PR status: {e}") from e
    
    def check_gh_cli_available(self) -> bool:
        """
        Check if GitHub CLI is installed and authenticated.
        
        DEPRECATED: Platform detection now uses API-based approach.
        
        Returns:
            True if gh CLI is available and authenticated
        """
        try:
            # Check if gh is installed
            self._run_command(['gh', '--version'])
            
            # Check if authenticated
            self._run_command(['gh', 'auth', 'status'])
            
            return True
        except RuntimeError:
            return False
    
    def generate_pr_body(
        self,
        session_id: str,
        files_changed: list[str],
        summary: Optional[str] = None
    ) -> str:
        """
        Generate a PR body with session information.
        
        Args:
            session_id: Session UUID
            files_changed: List of changed files
            summary: Optional summary of changes
            
        Returns:
            Formatted PR body text
        """
        body_parts = []
        
        if summary:
            body_parts.append(summary)
            body_parts.append("")
        
        body_parts.append("## Delegation Session Details")
        body_parts.append(f"- **Session ID**: `{session_id}`")
        body_parts.append(f"- **Files Changed**: {len(files_changed)}")
        body_parts.append("")
        
        if files_changed:
            body_parts.append("### Changed Files")
            for file in files_changed[:20]:  # Limit to first 20 files
                body_parts.append(f"- `{file}`")
            if len(files_changed) > 20:
                body_parts.append(f"- ... and {len(files_changed) - 20} more files")
            body_parts.append("")
        
        body_parts.append("---")
        body_parts.append("*Created by Agent CLI Orchestrator*")
        
        return "\n".join(body_parts)

