"""In-memory session storage with interface for database backends."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from src.session.models import Session, SessionStatus, SessionType


class SessionStore:
    """
    In-memory session storage.
    
    This class provides an interface designed for easy migration to database backends.
    All methods return results that can be easily serialized for API responses.
    """
    
    def __init__(self, default_ttl_hours: int = 24):
        """
        Initialize the session store.
        
        Args:
            default_ttl_hours: Default time-to-live for sessions in hours
        """
        self._sessions: Dict[UUID, Session] = {}
        self.default_ttl_hours = default_ttl_hours
    
    def create(self, session: Session) -> Session:
        """
        Create a new session.
        
        Args:
            session: Session object to store
            
        Returns:
            The stored session
            
        Raises:
            ValueError: If session with same ID already exists
        """
        if session.id in self._sessions:
            raise ValueError(f"Session with ID {session.id} already exists")
        
        # Set expiration if not set
        if session.expires_at is None:
            session.expires_at = datetime.utcnow() + timedelta(hours=self.default_ttl_hours)
        
        self._sessions[session.id] = session
        return session
    
    def get(self, session_id: UUID) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Session if found, None otherwise
        """
        session = self._sessions.get(session_id)
        
        # Check if session is expired
        if session and session.expires_at and datetime.utcnow() > session.expires_at:
            # Auto-expire the session
            if session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.ABANDONED
            return session
        
        return session
    
    def update(self, session: Session) -> Session:
        """
        Update an existing session.
        
        Args:
            session: Session object with updated data
            
        Returns:
            The updated session
            
        Raises:
            ValueError: If session doesn't exist
        """
        if session.id not in self._sessions:
            raise ValueError(f"Session with ID {session.id} not found")
        
        self._sessions[session.id] = session
        return session
    
    def delete(self, session_id: UUID) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: UUID of the session to delete
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list(
        self,
        user_id: Optional[str] = None,
        repo_name: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        status: Optional[SessionStatus] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Session]:
        """
        List sessions with optional filters.
        
        Args:
            user_id: Filter by user ID
            repo_name: Filter by repository name
            session_type: Filter by session type
            status: Filter by session status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching sessions
        """
        # Clean up expired sessions
        self._cleanup_expired()
        
        # Filter sessions
        sessions = list(self._sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        
        if repo_name:
            sessions = [s for s in sessions if s.repo_name == repo_name]
        
        if session_type:
            sessions = [s for s in sessions if s.type == session_type]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Sort by last activity (most recent first)
        sessions.sort(key=lambda s: s.last_activity_at, reverse=True)
        
        # Apply pagination
        if limit is not None:
            sessions = sessions[offset:offset + limit]
        else:
            sessions = sessions[offset:]
        
        return sessions
    
    def count(
        self,
        user_id: Optional[str] = None,
        repo_name: Optional[str] = None,
        session_type: Optional[SessionType] = None,
        status: Optional[SessionStatus] = None
    ) -> int:
        """
        Count sessions matching filters.
        
        Args:
            user_id: Filter by user ID
            repo_name: Filter by repository name
            session_type: Filter by session type
            status: Filter by session status
            
        Returns:
            Number of matching sessions
        """
        return len(self.list(user_id, repo_name, session_type, status))
    
    def _cleanup_expired(self):
        """Clean up expired sessions by marking them as abandoned."""
        now = datetime.utcnow()
        for session in self._sessions.values():
            if (session.expires_at and 
                now > session.expires_at and 
                session.status == SessionStatus.ACTIVE):
                session.status = SessionStatus.ABANDONED
    
    def clear(self):
        """Clear all sessions. Primarily for testing."""
        self._sessions.clear()
