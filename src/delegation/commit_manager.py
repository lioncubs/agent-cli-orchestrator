"""Git commit management for delegation workflows."""

import subprocess
from pathlib import Path
from typing import List, Optional

from src.session.models import GitIdentity


class CommitManager:
    """
    Manages Git commits for delegation sessions.
    
    Handles selective commits with proper author and committer identity management.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize commit manager.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
    
    def _run_git_command(
        self,
        command: list[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None
    ) -> str:
        """
        Run a git command and return output.
        
        Args:
            command: Git command as list of arguments
            cwd: Working directory for command (defaults to repo_path)
            env: Environment variables for command
            
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
                check=True,
                env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
    
    def get_changed_files(self, worktree_path: str) -> List[str]:
        """
        Get files modified, added, or deleted in worktree.
        
        Args:
            worktree_path: Path to the worktree
            
        Returns:
            List of changed file paths
        """
        path = Path(worktree_path)
        
        # Get staged and unstaged changes
        try:
            # Get status in porcelain format
            output = self._run_git_command(
                ['git', 'status', '--porcelain'],
                cwd=path
            )
        except RuntimeError:
            return []
        
        changed_files = []
        for line in output.split('\n'):
            if line.strip():
                # Format: XY filename
                # X = index status, Y = worktree status
                # Extract filename (skip first 3 chars: "XY ")
                filename = line[3:].strip()
                # Handle renames (format: "old -> new")
                if ' -> ' in filename:
                    filename = filename.split(' -> ')[1]
                changed_files.append(filename)
        
        return changed_files
    
    def commit_delegation_changes(
        self,
        worktree_path: str,
        user_identity: GitIdentity,
        agent_identity: GitIdentity,
        message: Optional[str] = None
    ) -> Optional[str]:
        """
        Commit changed files in delegation worktree.
        
        Sets GIT_AUTHOR_* from user_identity and GIT_COMMITTER_* from agent_identity.
        Only commits if there are changes.
        
        Args:
            worktree_path: Path to the worktree
            user_identity: Git identity for author (user who initiated delegation)
            agent_identity: Git identity for committer (agent making the commit)
            message: Optional commit message (auto-generated if not provided)
            
        Returns:
            Commit SHA if changes were committed, None if no changes
            
        Raises:
            RuntimeError: If commit fails
        """
        path = Path(worktree_path)
        
        # Check if there are any changes
        changed_files = self.get_changed_files(str(path))
        if not changed_files:
            return None
        
        # Stage all changes
        try:
            self._run_git_command(['git', 'add', '-A'], cwd=path)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to stage changes: {e}") from e
        
        # Generate commit message if not provided
        if not message:
            message = f"Delegation changes: {len(changed_files)} file(s) modified"
        
        # Prepare environment with author and committer identities
        import os
        env = os.environ.copy()
        env['GIT_AUTHOR_NAME'] = user_identity.name
        env['GIT_AUTHOR_EMAIL'] = user_identity.email
        env['GIT_COMMITTER_NAME'] = agent_identity.name
        env['GIT_COMMITTER_EMAIL'] = agent_identity.email
        
        # Create commit
        try:
            self._run_git_command(
                ['git', 'commit', '-m', message],
                cwd=path,
                env=env
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to commit changes: {e}") from e
        
        # Get the commit SHA
        try:
            commit_sha = self._run_git_command(
                ['git', 'rev-parse', 'HEAD'],
                cwd=path
            )
            return commit_sha
        except RuntimeError as e:
            raise RuntimeError(f"Failed to get commit SHA: {e}") from e
    
    def get_commit_info(self, worktree_path: str, commit_sha: str) -> dict:
        """
        Get information about a commit.
        
        Args:
            worktree_path: Path to the worktree
            commit_sha: Commit SHA
            
        Returns:
            Dictionary with commit information
        """
        path = Path(worktree_path)
        
        try:
            # Get commit details
            author = self._run_git_command(
                ['git', 'show', '-s', '--format=%an <%ae>', commit_sha],
                cwd=path
            )
            committer = self._run_git_command(
                ['git', 'show', '-s', '--format=%cn <%ce>', commit_sha],
                cwd=path
            )
            message = self._run_git_command(
                ['git', 'show', '-s', '--format=%s', commit_sha],
                cwd=path
            )
            date = self._run_git_command(
                ['git', 'show', '-s', '--format=%ci', commit_sha],
                cwd=path
            )
            
            return {
                'sha': commit_sha,
                'author': author,
                'committer': committer,
                'message': message,
                'date': date
            }
        except RuntimeError as e:
            raise RuntimeError(f"Failed to get commit info: {e}") from e
    
    def has_uncommitted_changes(self, worktree_path: str) -> bool:
        """
        Check if worktree has uncommitted changes.
        
        Args:
            worktree_path: Path to the worktree
            
        Returns:
            True if there are uncommitted changes
        """
        changed_files = self.get_changed_files(worktree_path)
        return len(changed_files) > 0
