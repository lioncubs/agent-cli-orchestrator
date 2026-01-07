"""Pull request management for delegation workflows."""

import subprocess
from pathlib import Path
from typing import Optional


class PRManager:
    """
    Manages pull request creation for delegation sessions.
    
    Integrates with GitHub CLI to create PRs from delegation branches.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize PR manager.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
    
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
    
    def create_pull_request(
        self,
        worktree_path: str,
        branch_name: str,
        base_branch: str,
        title: str,
        body: Optional[str] = None,
        draft: bool = False
    ) -> str:
        """
        Create a pull request using GitHub CLI.
        
        Args:
            worktree_path: Path to the worktree
            branch_name: Source branch name
            base_branch: Target base branch
            title: PR title
            body: PR description/body
            draft: If True, create as draft PR
            
        Returns:
            URL of created pull request
            
        Raises:
            RuntimeError: If PR creation fails
        """
        path = Path(worktree_path)
        
        # First, push the branch to remote
        try:
            self.push_branch(str(path), branch_name)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to push branch before creating PR: {e}") from e
        
        # Build gh pr create command
        command = [
            'gh', 'pr', 'create',
            '--base', base_branch,
            '--head', branch_name,
            '--title', title
        ]
        
        if body:
            command.extend(['--body', body])
        else:
            command.extend(['--body', ''])
        
        if draft:
            command.append('--draft')
        
        try:
            # Create PR and get URL
            pr_url = self._run_command(command, cwd=path)
            return pr_url
        except RuntimeError as e:
            raise RuntimeError(f"Failed to create pull request: {e}") from e
    
    def get_pr_status(self, worktree_path: str, pr_number: int) -> dict:
        """
        Get status of a pull request.
        
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
