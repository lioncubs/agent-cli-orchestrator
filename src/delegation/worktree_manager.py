"""Worktree management for delegation workflows."""

import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional
from uuid import UUID


class WorktreeManager:
    """
    Manages Git worktrees for delegation sessions.
    
    Provides isolation for concurrent delegation workflows by creating
    separate worktrees for each session.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize worktree manager.
        
        Args:
            repo_path: Path to the main Git repository
        """
        self.repo_path = Path(repo_path).resolve()
    
    def _run_git_command(self, command: list[str], cwd: Optional[Path] = None) -> str:
        """
        Run a git command and return output.
        
        Args:
            command: Git command as list of arguments
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
            raise RuntimeError(f"Git command failed: {e.stderr}") from e
    
    def create_delegation_worktree(
        self,
        repo_path: str,
        base_branch: str,
        session_id: UUID,
        user_id: str,
        task_slug: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create worktree for delegation session.
        
        Creates a new branch and worktree for isolated delegation work.
        Branch format: agent/<user_id>/<session_uuid_short>-<slug>
        
        Args:
            repo_path: Repository path (used as worktrees parent directory)
            base_branch: Base branch to branch from
            session_id: Session UUID
            user_id: User identifier
            task_slug: Optional task description slug
            
        Returns:
            Tuple of (worktree_path, branch_name)
            
        Raises:
            RuntimeError: If worktree creation fails
        """
        # Generate branch name
        session_short = str(session_id)[:8]
        if task_slug:
            branch_name = f"agent/{user_id}/{session_short}-{task_slug}"
        else:
            branch_name = f"agent/{user_id}/{session_short}"
        
        # Create worktree directory path
        worktrees_dir = Path(repo_path) / ".worktrees"
        worktrees_dir.mkdir(exist_ok=True)
        
        worktree_path = worktrees_dir / f"delegation-{session_id}"
        
        # Ensure base branch exists and is up to date
        try:
            # Fetch latest to ensure base_branch ref exists
            self._run_git_command(['git', 'fetch', 'origin', base_branch])
        except RuntimeError:
            # If fetch fails, base_branch might be local only
            pass
        
        # Create worktree with new branch based on base_branch
        try:
            self._run_git_command([
                'git', 'worktree', 'add',
                '-b', branch_name,
                str(worktree_path),
                base_branch
            ])
        except RuntimeError as e:
            # Cleanup partial worktree if it exists
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise RuntimeError(f"Failed to create delegation worktree: {e}") from e
        
        return str(worktree_path), branch_name
    
    def create_temp_worktree(
        self,
        repo_path: str,
        commit_sha: str,
        session_id: UUID
    ) -> str:
        """
        Create temporary worktree for research (detached HEAD).
        
        Used for read-only exploration without creating a branch.
        
        Args:
            repo_path: Repository path
            commit_sha: Commit SHA to checkout
            session_id: Session UUID
            
        Returns:
            Path to created worktree
            
        Raises:
            RuntimeError: If worktree creation fails
        """
        # Create worktree directory path
        worktrees_dir = Path(repo_path) / ".worktrees"
        worktrees_dir.mkdir(exist_ok=True)
        
        worktree_path = worktrees_dir / f"research-{session_id}"
        
        # Create worktree in detached HEAD state
        try:
            self._run_git_command([
                'git', 'worktree', 'add',
                '--detach',
                str(worktree_path),
                commit_sha
            ])
        except RuntimeError as e:
            # Cleanup partial worktree if it exists
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise RuntimeError(f"Failed to create temp worktree: {e}") from e
        
        return str(worktree_path)
    
    def cleanup_worktree(
        self,
        worktree_path: str,
        delete_branch: bool = False
    ) -> None:
        """
        Remove worktree and optionally delete associated branch.
        
        Args:
            worktree_path: Path to worktree to remove
            delete_branch: If True, also delete the branch
            
        Raises:
            RuntimeError: If cleanup fails
        """
        path = Path(worktree_path)
        
        if not path.exists():
            # Already cleaned up
            return
        
        # Get branch name before removing worktree (if needed for deletion)
        branch_name = None
        if delete_branch:
            try:
                branch_name = self._run_git_command(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=path
                )
            except RuntimeError:
                # Detached HEAD or other issue, no branch to delete
                pass
        
        # Remove worktree
        try:
            self._run_git_command(['git', 'worktree', 'remove', str(path), '--force'])
        except RuntimeError as e:
            # If git worktree remove fails, try manual cleanup
            try:
                shutil.rmtree(path, ignore_errors=True)
                # Prune worktree from git's records
                self._run_git_command(['git', 'worktree', 'prune'])
            except Exception as cleanup_error:
                raise RuntimeError(f"Failed to cleanup worktree: {e}") from cleanup_error
        
        # Delete branch if requested and not detached HEAD
        if delete_branch and branch_name and branch_name != 'HEAD':
            try:
                self._run_git_command(['git', 'branch', '-D', branch_name])
            except RuntimeError:
                # Branch deletion is best-effort
                pass
    
    def list_worktrees(self) -> list[dict[str, str]]:
        """
        List all worktrees in the repository.
        
        Returns:
            List of worktree information dictionaries
        """
        try:
            output = self._run_git_command(['git', 'worktree', 'list', '--porcelain'])
        except RuntimeError:
            return []
        
        worktrees = []
        current_worktree = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                if current_worktree:
                    worktrees.append(current_worktree)
                    current_worktree = {}
            elif line.startswith('worktree '):
                if current_worktree:
                    worktrees.append(current_worktree)
                current_worktree = {'path': line.split(' ', 1)[1]}
            elif line.startswith('branch '):
                branch_ref = line.split(' ', 1)[1]
                current_worktree['branch'] = branch_ref.replace('refs/heads/', '')
            elif line.startswith('HEAD '):
                current_worktree['HEAD'] = line.split(' ', 1)[1]
            elif line.startswith('detached'):
                current_worktree['detached'] = True
        
        # Don't forget the last worktree
        if current_worktree:
            worktrees.append(current_worktree)
        
        return worktrees
