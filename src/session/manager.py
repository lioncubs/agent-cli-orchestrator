"""Session lifecycle management."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4, UUID
from pathlib import Path

from src.session.models import (
    Session,
    SessionType,
    SessionStatus,
    Turn,
    GitIdentity
)
from src.session.store import SessionStore
from src.integrations.git import GitOperations
from src.integrations.copilot import CopilotCLI


class SessionManager:
    """
    Manages session lifecycle including creation, continuation, and expiration.
    
    Integrates with Git operations and Copilot CLI for delegation/research sessions.
    """
    
    def __init__(
        self,
        store: SessionStore,
        git_ops: Optional[GitOperations] = None,
        copilot_cli: Optional[CopilotCLI] = None
    ):
        """
        Initialize session manager.
        
        Args:
            store: Session store instance
            git_ops: Git operations instance (optional)
            copilot_cli: Copilot CLI instance (optional)
        """
        self.store = store
        self.git_ops = git_ops
        self.copilot_cli = copilot_cli
    
    def create_session(
        self,
        session_type: SessionType,
        repo_name: str,
        user_id: str,
        user_identity: Optional[GitIdentity] = None,
        base_branch: Optional[str] = None,
        is_temporary: bool = False,
        ttl_hours: Optional[int] = None
    ) -> Session:
        """
        Create a new session.
        
        Args:
            session_type: Type of session (query, research, delegation)
            repo_name: Repository name
            user_id: User identifier
            user_identity: Git user identity (name and email)
            base_branch: Base branch for research/delegation sessions
            is_temporary: Whether this is a temporary session
            ttl_hours: Custom time-to-live in hours
            
        Returns:
            Created session
        """
        now = datetime.utcnow()
        expires_at = None
        if ttl_hours:
            expires_at = now + timedelta(hours=ttl_hours)
        
        session = Session(
            id=uuid4(),
            type=session_type,
            status=SessionStatus.ACTIVE,
            repo_name=repo_name,
            user_id=user_id,
            user_identity=user_identity,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            base_branch=base_branch,
            is_temporary=is_temporary,
            turns=[],
            files_changed=[]
        )
        
        # For research/delegation sessions, capture base commit
        if session_type in [SessionType.RESEARCH, SessionType.DELEGATION]:
            if self.git_ops and base_branch:
                try:
                    # Get current commit on base branch
                    session.base_commit = self._get_branch_commit(base_branch)
                except Exception as e:
                    # Log error but don't fail session creation
                    pass
        
        return self.store.create(session)
    
    def get_session(self, session_id: UUID) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Session if found, None otherwise
        """
        return self.store.get(session_id)
    
    def continue_session(
        self,
        session_id: UUID,
        prompt: str,
        response: str,
        response_summary: str,
        files_analyzed: Optional[list] = None,
        files_changed: Optional[list] = None,
        copilot_session_id: Optional[str] = None
    ) -> Session:
        """
        Continue a session by adding a new turn.
        
        Args:
            session_id: Session UUID
            prompt: User prompt
            response: System response
            response_summary: Summary of the response
            files_analyzed: List of files analyzed
            files_changed: List of files changed
            copilot_session_id: Copilot session ID if applicable
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If session not found or not active
        """
        session = self.store.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active (status: {session.status})")
        
        # Create new turn
        turn = Turn(
            id=len(session.turns) + 1,
            prompt=prompt,
            response=response,
            response_summary=response_summary,
            files_analyzed=files_analyzed or [],
            files_changed=files_changed or [],
            timestamp=datetime.utcnow()
        )
        
        # Update session
        session.turns.append(turn)
        session.last_activity_at = datetime.utcnow()
        
        # Update copilot session ID if provided
        if copilot_session_id:
            session.copilot_session_id = copilot_session_id
        
        # Update files changed at session level
        if files_changed:
            for file in files_changed:
                if file not in session.files_changed:
                    session.files_changed.append(file)
        
        return self.store.update(session)
    
    def complete_session(
        self,
        session_id: UUID,
        commit_sha: Optional[str] = None,
        pr_url: Optional[str] = None
    ) -> Session:
        """
        Mark a session as completed.
        
        Args:
            session_id: Session UUID
            commit_sha: Commit SHA if changes were committed
            pr_url: Pull request URL if PR was created
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If session not found
        """
        session = self.store.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update status based on what was done
        if pr_url:
            session.status = SessionStatus.PR_CREATED
            session.pr_url = pr_url
        elif commit_sha:
            session.status = SessionStatus.COMMITTED
            session.commit_sha = commit_sha
        else:
            session.status = SessionStatus.COMPLETED
        
        session.last_activity_at = datetime.utcnow()
        
        return self.store.update(session)
    
    def abandon_session(self, session_id: UUID) -> Session:
        """
        Abandon a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If session not found
        """
        session = self.store.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = SessionStatus.ABANDONED
        session.last_activity_at = datetime.utcnow()
        
        return self.store.update(session)
    
    def close_session(self, session_id: UUID) -> Session:
        """
        Close a session (soft delete - marks as closed but keeps in store).
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated session
            
        Raises:
            ValueError: If session not found
        """
        session = self.store.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = SessionStatus.CLOSED
        session.last_activity_at = datetime.utcnow()
        
        return self.store.update(session)
    
    def delete_session(self, session_id: UUID) -> bool:
        """
        Permanently delete a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if deleted, False if not found
        """
        return self.store.delete(session_id)
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        repo_name: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list:
        """
        List sessions with filters.
        
        Args:
            user_id: Filter by user ID
            repo_name: Filter by repository name
            session_type: Filter by session type
            status: Filter by session status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of sessions
        """
        return self.store.list(user_id, repo_name, session_type, status, limit, offset)
    
    def _get_branch_commit(self, branch: str) -> str:
        """
        Get the current commit SHA of a branch.
        
        Args:
            branch: Branch name
            
        Returns:
            Commit SHA
        """
        if not self.git_ops:
            raise RuntimeError("Git operations not available")
        
        # Use git rev-parse to get commit SHA
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', branch],
            cwd=self.git_ops.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
