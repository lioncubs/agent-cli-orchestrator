"""Git configuration management for identity injection."""

import subprocess
from pathlib import Path
from typing import Optional

from src.session.models import GitIdentity


class GitConfigManager:
    """Manager for injecting Git identity into operations."""
    
    def __init__(self, repo_path: str):
        """
        Initialize Git configuration manager.
        
        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path)
    
    def set_local_identity(self, identity: GitIdentity) -> bool:
        """
        Set the local Git identity for the repository.
        
        Args:
            identity: Git identity to configure
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set local user name
            subprocess.run(
                ["git", "config", "--local", "user.name", identity.name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Set local user email
            subprocess.run(
                ["git", "config", "--local", "user.email", identity.email],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_local_identity(self) -> Optional[GitIdentity]:
        """
        Get the local Git identity from the repository.
        
        Returns:
            GitIdentity if configured, None otherwise
        """
        try:
            # Get user name
            name_result = subprocess.run(
                ["git", "config", "--local", "user.name"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            name = name_result.stdout.strip()
            
            # Get user email
            email_result = subprocess.run(
                ["git", "config", "--local", "user.email"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            email = email_result.stdout.strip()
            
            if name and email:
                return GitIdentity(name=name, email=email)
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    def unset_local_identity(self) -> bool:
        """
        Remove the local Git identity from the repository.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Unset user name
            subprocess.run(
                ["git", "config", "--local", "--unset", "user.name"],
                cwd=self.repo_path,
                check=False,
                capture_output=True
            )
            
            # Unset user email
            subprocess.run(
                ["git", "config", "--local", "--unset", "user.email"],
                cwd=self.repo_path,
                check=False,
                capture_output=True
            )
            
            return True
        except Exception:
            return False
    
    def set_worktree_identity(
        self,
        worktree_path: str,
        identity: GitIdentity
    ) -> bool:
        """
        Set the Git identity for a specific worktree.
        
        Args:
            worktree_path: Path to the worktree
            identity: Git identity to configure
            
        Returns:
            True if successful, False otherwise
        """
        try:
            worktree = Path(worktree_path)
            
            # Set user name in worktree
            subprocess.run(
                ["git", "config", "--local", "user.name", identity.name],
                cwd=worktree,
                check=True,
                capture_output=True
            )
            
            # Set user email in worktree
            subprocess.run(
                ["git", "config", "--local", "user.email", identity.email],
                cwd=worktree,
                check=True,
                capture_output=True
            )
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def create_commit_env(identity: GitIdentity) -> dict[str, str]:
        """
        Create environment variables for Git commits with specific identity.
        
        Args:
            identity: Git identity to use
            
        Returns:
            Dictionary of environment variables for Git commands
        """
        return {
            "GIT_AUTHOR_NAME": identity.name,
            "GIT_AUTHOR_EMAIL": identity.email,
            "GIT_COMMITTER_NAME": identity.name,
            "GIT_COMMITTER_EMAIL": identity.email,
        }
