"""Session management MCP tools."""

from typing import Dict, Any, List
from uuid import UUID

from src.mcp.models import (
    ContinueSessionInput,
    ListSessionsInput,
    GetSessionInput,
    CloseSessionInput,
    TurnResult,
    SessionResult,
    MCPError
)
from src.session.manager import SessionManager
from src.session.store import SessionStore
from src.session.models import SessionStatus


class SessionTools:
    """MCP tools for session management."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        session_store: SessionStore
    ):
        """
        Initialize session tools.
        
        Args:
            session_manager: Session manager
            session_store: Session storage
        """
        self.session_manager = session_manager
        self.session_store = session_store
    
    async def continue_session(self, input_data: ContinueSessionInput) -> Dict[str, Any]:
        """
        Continue an existing session with a follow-up prompt.
        
        Args:
            input_data: Session continuation parameters
            
        Returns:
            TurnResult with response
        """
        try:
            result = await self.session_manager.continue_session(
                session_id=input_data.session_id,
                prompt=input_data.prompt
            )
            
            return TurnResult(
                turn_id=result.get("turn_id", 1),
                prompt=input_data.prompt,
                response=result.get("response", ""),
                response_summary=result.get("response_summary", ""),
                files_analyzed=result.get("files_analyzed", []),
                files_changed=result.get("files_changed", []),
                timestamp=result.get("timestamp")
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to continue session",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
    
    async def list_sessions(self, input_data: ListSessionsInput) -> Dict[str, Any]:
        """
        List sessions with optional filters.
        
        Args:
            input_data: Filter parameters
            
        Returns:
            List of SessionResults
        """
        try:
            # Get all sessions
            sessions = await self.session_store.list_sessions(
                type=input_data.type,
                status=input_data.status,
                repo_name=input_data.repo_name
            )
            
            # Filter by user if specified
            if input_data.user_id:
                sessions = [s for s in sessions if s.user_id == input_data.user_id]
            
            # Limit results
            sessions = sessions[:input_data.limit]
            
            results = [
                SessionResult(
                    session_id=s.id,
                    type=s.type,
                    status=s.status,
                    repo_name=s.repo_name,
                    user_id=s.user_id,
                    created_at=s.created_at,
                    last_activity_at=s.last_activity_at,
                    base_branch=s.base_branch,
                    session_branch=s.session_branch,
                    worktree_path=s.worktree_path,
                    turns_count=len(s.turns),
                    files_changed=s.files_changed,
                    pr_url=s.pr_url
                ).model_dump()
                for s in sessions
            ]
            
            return {
                "sessions": results,
                "total": len(results)
            }
            
        except Exception as e:
            return MCPError(
                error="Failed to list sessions",
                details=str(e)
            ).model_dump()
    
    async def get_session(self, input_data: GetSessionInput) -> Dict[str, Any]:
        """
        Get details of a specific session.
        
        Args:
            input_data: Session ID
            
        Returns:
            SessionResult with full details
        """
        try:
            session = await self.session_store.get_session(input_data.session_id)
            
            if not session:
                return MCPError(
                    error="Session not found",
                    session_id=input_data.session_id
                ).model_dump()
            
            return SessionResult(
                session_id=session.id,
                type=session.type,
                status=session.status,
                repo_name=session.repo_name,
                user_id=session.user_id,
                created_at=session.created_at,
                last_activity_at=session.last_activity_at,
                base_branch=session.base_branch,
                session_branch=session.session_branch,
                worktree_path=session.worktree_path,
                turns_count=len(session.turns),
                files_changed=session.files_changed,
                pr_url=session.pr_url
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to get session",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
    
    async def close_session(self, input_data: CloseSessionInput) -> Dict[str, Any]:
        """
        Close or abandon a session.
        
        Args:
            input_data: Close session parameters
            
        Returns:
            Success message
        """
        try:
            session = await self.session_store.get_session(input_data.session_id)
            
            if not session:
                return MCPError(
                    error="Session not found",
                    session_id=input_data.session_id
                ).model_dump()
            
            # Update status
            new_status = SessionStatus.ABANDONED if input_data.abandon else SessionStatus.CLOSED
            session.status = new_status
            await self.session_store.update_session(session)
            
            # Clean up if needed (worktrees, etc.)
            await self.session_manager.cleanup_session(input_data.session_id)
            
            return {
                "success": True,
                "session_id": str(input_data.session_id),
                "status": new_status.value,
                "message": f"Session {'abandoned' if input_data.abandon else 'closed'} successfully"
            }
            
        except Exception as e:
            return MCPError(
                error="Failed to close session",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
