"""Git operations module for managing branches and worktrees."""

import subprocess
from pathlib import Path
from typing import List, Dict, Union


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
    
    def get_status(self) -> Dict[str, any]:
        """Get detailed git status including modified, staged, and untracked files."""
        try:
            # Get porcelain status for parsing
            output = self._run_command(['git', 'status', '--porcelain'])
            
            modified = []
            staged = []
            untracked = []
            conflicts = []
            
            for line in output.split('\n'):
                if not line:
                    continue
                # Status format: XY filename
                # X = index status, Y = working tree status
                index_status = line[0] if len(line) > 0 else ' '
                work_status = line[1] if len(line) > 1 else ' '
                filename = line[3:] if len(line) > 3 else ''
                
                # Untracked files
                if index_status == '?' and work_status == '?':
                    untracked.append(filename)
                # Merge conflicts
                elif index_status == 'U' or work_status == 'U' or (index_status == 'A' and work_status == 'A') or (index_status == 'D' and work_status == 'D'):
                    conflicts.append(filename)
                else:
                    # Staged changes (index has changes)
                    if index_status in 'MADRC':
                        staged.append(filename)
                    # Modified in working tree
                    if work_status in 'MD':
                        modified.append(filename)
            
            return {
                'is_clean': len(modified) == 0 and len(staged) == 0 and len(conflicts) == 0,
                'modified': modified,
                'staged': staged,
                'untracked': untracked,
                'conflicts': conflicts,
                'has_conflicts': len(conflicts) > 0,
                'has_staged': len(staged) > 0,
                'has_modified': len(modified) > 0
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get git status: {e.stderr}")
    
    def is_working_tree_clean(self) -> bool:
        """Check if working tree is clean (no uncommitted changes)."""
        status = self.get_status()
        return status['is_clean']
    
    def switch_branch(self, branch_name: str, force: bool = False) -> Dict[str, any]:
        """
        Switch to a different branch.
        
        Args:
            branch_name: The name of the branch to switch to
            force: If True, discard local changes and force switch
            
        Returns:
            Dict with status, branch name, and message
            
        Raises:
            RuntimeError: If branch switch fails or working tree is dirty
        """
        try:
            # Check current branch first
            current_branch = self.get_current_branch()
            if current_branch == branch_name:
                return {
                    "status": "success",
                    "branch": branch_name,
                    "message": f"Already on branch '{branch_name}'",
                    "was_switch_needed": False
                }
            
            # Check if working tree is clean (unless force is True)
            if not force:
                status = self.get_status()
                
                if status['has_conflicts']:
                    raise RuntimeError(
                        f"Cannot switch branches: You have merge conflicts in {len(status['conflicts'])} file(s).\n"
                        f"Conflicted files: {', '.join(status['conflicts'][:5])}{'...' if len(status['conflicts']) > 5 else ''}\n\n"
                        f"To fix this:\n"
                        f"  1. Resolve the conflicts in the listed files\n"
                        f"  2. Stage the resolved files: git add <file>\n"
                        f"  3. Complete the merge: git commit\n\n"
                        f"Or abort the merge: git merge --abort"
                    )
                
                if status['has_staged']:
                    raise RuntimeError(
                        f"Cannot switch branches: You have {len(status['staged'])} staged change(s).\n"
                        f"Staged files: {', '.join(status['staged'][:5])}{'...' if len(status['staged']) > 5 else ''}\n\n"
                        f"To fix this, choose one option:\n"
                        f"  • Commit your changes: git commit -m 'Your message'\n"
                        f"  • Stash your changes: git stash\n"
                        f"  • Unstage changes: git reset HEAD\n"
                        f"  • Discard changes: git checkout -- . (WARNING: loses changes)"
                    )
                
                if status['has_modified']:
                    raise RuntimeError(
                        f"Cannot switch branches: You have {len(status['modified'])} modified file(s).\n"
                        f"Modified files: {', '.join(status['modified'][:5])}{'...' if len(status['modified']) > 5 else ''}\n\n"
                        f"To fix this, choose one option:\n"
                        f"  • Commit your changes:\n"
                        f"      git add .\n"
                        f"      git commit -m 'Your message'\n"
                        f"  • Stash your changes: git stash\n"
                        f"  • Discard changes: git checkout -- . (WARNING: loses changes)"
                    )
            
            # Perform the switch
            cmd = ['git', 'checkout']
            if force:
                cmd.append('-f')
            cmd.append(branch_name)
            
            self._run_command(cmd)
            return {
                "status": "success",
                "branch": branch_name,
                "message": f"Switched to branch '{branch_name}'",
                "was_switch_needed": True,
                "previous_branch": current_branch
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            
            # Check for common errors and provide helpful messages
            if "did not match any" in error_msg or "pathspec" in error_msg:
                raise RuntimeError(
                    f"Branch '{branch_name}' does not exist.\n\n"
                    f"To fix this:\n"
                    f"  • List available branches: git branch -a\n"
                    f"  • Create the branch: git checkout -b {branch_name}\n"
                    f"  • Fetch remote branches: git fetch --all"
                )
            elif "would be overwritten" in error_msg:
                raise RuntimeError(
                    f"Cannot switch branches: Local changes would be overwritten.\n\n"
                    f"To fix this:\n"
                    f"  • Commit your changes: git add . && git commit -m 'message'\n"
                    f"  • Stash your changes: git stash\n"
                    f"  • Discard changes: git checkout -- ."
                )
            else:
                raise RuntimeError(f"Failed to switch branch: {error_msg}")
    
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