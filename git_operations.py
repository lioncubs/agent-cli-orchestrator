"""Git operations module for managing branches and worktrees."""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union


class GitOperations:
    """Handle Git operations for branches and worktrees."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
    
    def _run_command(self, command: List[str]) -> str:
        """Run a git command and return output."""
        result = subprocess.run(
            command,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    
    def get_current_branch(self) -> str:
        """Get the current branch name."""
        try:
            return self._run_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get current branch: {e.stderr}")
    
    def switch_branch(self, branch_name: str) -> Dict[str, str]:
        """Switch to a different branch."""
        try:
            self._run_command(['git', 'checkout', branch_name])
            return {
                "status": "success",
                "branch": branch_name,
                "message": f"Switched to branch '{branch_name}'"
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to switch branch: {e.stderr}")
    
    def list_worktrees(self) -> List[Dict[str, str]]:
        """List all Git worktrees."""
        try:
            output = self._run_command(['git', 'worktree', 'list', '--porcelain'])
            worktrees = []
            current_worktree = {}
            
            if not output or output.strip() == '':
                # No worktrees or empty output, return empty list
                return worktrees
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    # Empty line separates worktrees
                    if current_worktree:
                        worktrees.append(current_worktree)
                        current_worktree = {}
                elif line.startswith('worktree '):
                    if current_worktree:
                        worktrees.append(current_worktree)
                    current_worktree = {'path': line.split(' ', 1)[1]}
                elif line.startswith('branch '):
                    current_worktree['branch'] = line.split('refs/heads/', 1)[1] if 'refs/heads/' in line else line.split(' ', 1)[1]
                elif line.startswith('HEAD '):
                    current_worktree['HEAD'] = line.split(' ', 1)[1]
                elif line.startswith('bare'):
                    current_worktree['bare'] = True
                elif line.startswith('detached'):
                    current_worktree['detached'] = True
            
            # Don't forget the last worktree
            if current_worktree:
                worktrees.append(current_worktree)
            
            return worktrees
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list worktrees: {e.stderr}")
    
    def create_worktree(self, path: str, branch: str, create_branch: bool = False) -> Dict[str, str]:
        """Create a new Git worktree."""
        try:
            command = ['git', 'worktree', 'add']
            if create_branch:
                command.extend(['-b', branch])
            command.append(path)
            if not create_branch:
                command.append(branch)
            
            self._run_command(command)
            return {
                "status": "success",
                "path": path,
                "branch": branch,
                "message": f"Worktree created at '{path}' for branch '{branch}'"
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create worktree: {e.stderr}")
    
    def list_branches(self) -> List[Dict[str, Union[str, bool]]]:
        """List all Git branches (both local and remote)."""
        try:
            # Get local branches
            local_output = self._run_command(['git', 'branch', '--format=%(refname:short)|%(HEAD)'])
            branches = []
            
            for line in local_output.split('\n'):
                if line:
                    parts = line.split('|')
                    branch_name = parts[0]
                    is_current = parts[1] == '*' if len(parts) > 1 else False
                    branches.append({
                        'name': branch_name,
                        'current': is_current,
                        'type': 'local'
                    })
            
            # Get remote branches
            try:
                remote_output = self._run_command(['git', 'branch', '-r', '--format=%(refname:short)'])
                for line in remote_output.split('\n'):
                    if line and not line.endswith('/HEAD'):
                        branches.append({
                            'name': line,
                            'current': False,
                            'type': 'remote'
                        })
            except subprocess.CalledProcessError:
                pass  # Remote branches may not exist
            
            return branches
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list branches: {e.stderr}")
    
    def get_repository_name(self) -> str:
        """Get the repository name from Git remote."""
        try:
            remote_url = self._run_command(['git', 'config', '--get', 'remote.origin.url'])
            # Extract repo name from URL (handles both https and ssh)
            if remote_url:
                repo_name = remote_url.split('/')[-1].replace('.git', '')
                return repo_name
            return "unknown"
        except subprocess.CalledProcessError:
            return "unknown"