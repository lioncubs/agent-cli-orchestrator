"""Delegation service orchestrating the complete delegation lifecycle."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pathlib import Path

from src.session.models import Session, SessionStatus, GitIdentity
from src.session.store import SessionStore
from src.delegation.worktree_manager import WorktreeManager
from src.delegation.commit_manager import CommitManager
from src.delegation.pr_manager import PRManager


class DelegationService:
    """
    Orchestrates the complete delegation lifecycle.
    
    Manages initialization, workload distribution, status transitions,
    and cleanup for delegation sessions.
    """
    
    def __init__(
        self,
        session_store: SessionStore,
        repo_path: str = ".",
        agent_identity: Optional[GitIdentity] = None
    ):
        """
        Initialize delegation service.
        
        Args:
            session_store: Session store instance
            repo_path: Path to Git repository
            agent_identity: Default agent identity for commits
        """
        self.session_store = session_store
        self.repo_path = Path(repo_path).resolve()
        self.worktree_manager = WorktreeManager(str(self.repo_path))
        self.commit_manager = CommitManager(str(self.repo_path))
        self.pr_manager = PRManager(str(self.repo_path))
        
        # Default agent identity
        self.agent_identity = agent_identity or GitIdentity(
            name="Agent CLI Orchestrator",
            email="agent@cli-orchestrator.local"
        )
    
    def initialize_delegation(
        self,
        session: Session,
        task_slug: Optional[str] = None
    ) -> Session:
        """
        Initialize delegation by creating worktree and branch.
        
        Args:
            session: Session to initialize
            task_slug: Optional task description slug for branch name
            
        Returns:
            Updated session with worktree and branch information
            
        Raises:
            ValueError: If session is not a delegation session
            RuntimeError: If initialization fails
        """
        from src.session.models import SessionType
        
        if session.type != SessionType.DELEGATION:
            raise ValueError(f"Session {session.id} is not a delegation session")
        
        if not session.base_branch:
            raise ValueError("Base branch is required for delegation")
        
        if not session.user_identity:
            raise ValueError("User identity is required for delegation")
        
        # Create delegation worktree
        try:
            worktree_path, branch_name = self.worktree_manager.create_delegation_worktree(
                repo_path=str(self.repo_path),
                base_branch=session.base_branch,
                session_id=session.id,
                user_id=session.user_id,
                task_slug=task_slug
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to create delegation worktree: {e}") from e
        
        # Update session with worktree information
        session.worktree_path = worktree_path
        session.session_branch = branch_name
        
        # Get base commit SHA
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'rev-parse', session.base_branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            session.base_commit = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass  # base_commit is optional
        
        return self.session_store.update(session)
    
    def commit_changes(
        self,
        session: Session,
        message: Optional[str] = None
    ) -> Session:
        """
        Commit changes in delegation worktree.
        
        Args:
            session: Delegation session
            message: Optional commit message
            
        Returns:
            Updated session with commit information
            
        Raises:
            ValueError: If session state is invalid
            RuntimeError: If commit fails
        """
        if not session.worktree_path:
            raise ValueError("Session has no worktree")
        
        if not session.user_identity:
            raise ValueError("Session has no user identity")
        
        # Get changed files before committing
        changed_files = self.commit_manager.get_changed_files(session.worktree_path)
        
        if not changed_files:
            # No changes to commit
            return session
        
        # Commit changes with user as author and agent as committer
        try:
            commit_sha = self.commit_manager.commit_delegation_changes(
                worktree_path=session.worktree_path,
                user_identity=session.user_identity,
                agent_identity=self.agent_identity,
                message=message
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to commit changes: {e}") from e
        
        if commit_sha:
            # Update session with commit information
            session.commit_sha = commit_sha
            session.files_changed = changed_files
            session.status = SessionStatus.COMMITTED
            session.last_activity_at = datetime.utcnow()
            
            return self.session_store.update(session)
        
        return session
    
    async def create_pull_request(
        self,
        session: Session,
        title: str,
        body: Optional[str] = None,
        draft: bool = False,
        repo_identifier: Optional[str] = None,
    ) -> Session:
        """
        Create pull request for delegation changes.
        
        Args:
            session: Delegation session with committed changes
            title: PR title
            body: PR description (auto-generated if not provided)
            draft: If True, create as draft PR
            repo_identifier: Repository identifier (auto-detected if not provided)
            
        Returns:
            Updated session with PR information
            
        Raises:
            ValueError: If session state is invalid
            RuntimeError: If PR creation fails
        """
        if not session.worktree_path:
            raise ValueError("Session has no worktree")
        
        if not session.session_branch:
            raise ValueError("Session has no branch")
        
        if not session.base_branch:
            raise ValueError("Session has no base branch")
        
        if not session.commit_sha:
            raise ValueError("Session has no commits (commit changes first)")
        
        # Generate PR body if not provided
        if not body:
            body = self.pr_manager.generate_pr_body(
                session_id=str(session.id),
                files_changed=session.files_changed,
                summary=f"Delegation session for {session.user_id}"
            )
        
        # Create pull request
        try:
            pr_result = await self.pr_manager.create_pull_request(
                worktree_path=session.worktree_path,
                branch_name=session.session_branch,
                base_branch=session.base_branch,
                title=title,
                body=body,
                draft=draft,
                repo_identifier=repo_identifier,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to create pull request: {e}") from e
        
        # Update session with PR information
        session.pr_url = pr_result.get("pr_url")
        session.status = SessionStatus.PR_CREATED
        session.last_activity_at = datetime.utcnow()
        
        return self.session_store.update(session)
    
    def abandon_delegation(self, session: Session, delete_branch: bool = True) -> Session:
        """
        Abandon delegation and clean up worktree.
        
        Args:
            session: Delegation session to abandon
            delete_branch: If True, delete the branch (default: True)
            
        Returns:
            Updated session marked as abandoned
        """
        # Cleanup worktree if it exists
        if session.worktree_path:
            try:
                self.worktree_manager.cleanup_worktree(
                    worktree_path=session.worktree_path,
                    delete_branch=delete_branch
                )
            except RuntimeError:
                # Best-effort cleanup
                pass
        
        # Update session status
        session.status = SessionStatus.ABANDONED
        session.last_activity_at = datetime.utcnow()
        
        return self.session_store.update(session)
    
    def get_delegation_status(self, session: Session) -> Dict[str, Any]:
        """
        Get current status of delegation session.
        
        Args:
            session: Delegation session
            
        Returns:
            Dictionary with delegation status information
        """
        status = {
            'session_id': str(session.id),
            'status': session.status.value,
            'base_branch': session.base_branch,
            'session_branch': session.session_branch,
            'worktree_path': session.worktree_path,
            'commit_sha': session.commit_sha,
            'pr_url': session.pr_url,
            'files_changed': session.files_changed,
            'has_uncommitted_changes': False
        }
        
        # Check for uncommitted changes if worktree exists
        if session.worktree_path:
            try:
                status['has_uncommitted_changes'] = self.commit_manager.has_uncommitted_changes(
                    session.worktree_path
                )
            except RuntimeError:
                pass
        
        return status
