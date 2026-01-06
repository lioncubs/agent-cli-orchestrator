"""API routes for session management."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.session.models import (
    Session,
    SessionType,
    SessionStatus,
    GitIdentity
)
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.integrations.git import GitOperations
from src.integrations.copilot import CopilotCLI


# Request/Response Models
class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    type: SessionType
    repo_name: str
    user_id: str
    user_identity: Optional[GitIdentity] = None
    base_branch: Optional[str] = None
    is_temporary: bool = False
    ttl_hours: Optional[int] = None


class ContinueSessionRequest(BaseModel):
    """Request to continue a session."""
    prompt: str
    response_summary: Optional[str] = None
    files_analyzed: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Response containing session data."""
    session: Session
    message: str = "Success"


class SessionListResponse(BaseModel):
    """Response for listing sessions."""
    sessions: List[Session]
    total: int
    limit: Optional[int]
    offset: int


class DeleteSessionResponse(BaseModel):
    """Response for session deletion."""
    success: bool
    message: str


# Initialize router
router = APIRouter(prefix="/sessions", tags=["sessions"])

# Global instances (to be initialized by main app)
_session_store: Optional[SessionStore] = None
_session_manager: Optional[SessionManager] = None


def init_session_routes(
    session_store: SessionStore,
    session_manager: SessionManager
):
    """
    Initialize session routes with required dependencies.
    
    Args:
        session_store: SessionStore instance
        session_manager: SessionManager instance
    """
    global _session_store, _session_manager
    _session_store = session_store
    _session_manager = session_manager


def _get_manager() -> SessionManager:
    """Get the session manager instance."""
    if _session_manager is None:
        raise HTTPException(
            status_code=500,
            detail="Session manager not initialized"
        )
    return _session_manager


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest):
    """
    Create a new session.
    
    Args:
        request: Session creation request
        
    Returns:
        Created session
    """
    manager = _get_manager()
    
    try:
        session = manager.create_session(
            session_type=request.type,
            repo_name=request.repo_name,
            user_id=request.user_id,
            user_identity=request.user_identity,
            base_branch=request.base_branch,
            is_temporary=request.is_temporary,
            ttl_hours=request.ttl_hours
        )
        
        return SessionResponse(
            session=session,
            message=f"Session {session.id} created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    repo_name: Optional[str] = Query(None, description="Filter by repository name"),
    session_type: Optional[SessionType] = Query(None, description="Filter by session type"),
    status: Optional[SessionStatus] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset")
):
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
        List of sessions matching filters
    """
    manager = _get_manager()
    
    try:
        sessions = manager.list_sessions(
            user_id=user_id,
            repo_name=repo_name,
            session_type=session_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        total = manager.store.count(
            user_id=user_id,
            repo_name=repo_name,
            session_type=session_type,
            status=status
        )
        
        return SessionListResponse(
            sessions=sessions,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID):
    """
    Get detailed session information.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Session details
    """
    manager = _get_manager()
    
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    return SessionResponse(session=session)


@router.post("/{session_id}/continue", response_model=SessionResponse)
async def continue_session(session_id: UUID, request: ContinueSessionRequest):
    """
    Continue a session with a new prompt/response turn.
    
    Args:
        session_id: Session UUID
        request: Continue session request
        
    Returns:
        Updated session
    """
    manager = _get_manager()
    
    try:
        # If response_summary not provided, use a truncated version of prompt
        response_summary = request.response_summary or request.prompt[:200]
        
        session = manager.continue_session(
            session_id=session_id,
            prompt=request.prompt,
            response="",  # To be filled by actual copilot response
            response_summary=response_summary,
            files_analyzed=request.files_analyzed,
            files_changed=request.files_changed
        )
        
        return SessionResponse(
            session=session,
            message=f"Session {session_id} continued successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(
    session_id: UUID,
    abandon: bool = Query(False, description="Mark as abandoned instead of deleting")
):
    """
    Delete or abandon a session.
    
    Args:
        session_id: Session UUID
        abandon: If True, mark as abandoned; if False, permanently delete
        
    Returns:
        Deletion result
    """
    manager = _get_manager()
    
    try:
        if abandon:
            session = manager.abandon_session(session_id)
            return DeleteSessionResponse(
                success=True,
                message=f"Session {session_id} marked as abandoned"
            )
        else:
            success = manager.delete_session(session_id)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            return DeleteSessionResponse(
                success=True,
                message=f"Session {session_id} deleted successfully"
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    commit_sha: Optional[str] = Query(None, description="Commit SHA if committed"),
    pr_url: Optional[str] = Query(None, description="PR URL if created")
):
    """
    Mark a session as completed.
    
    Args:
        session_id: Session UUID
        commit_sha: Optional commit SHA
        pr_url: Optional PR URL
        
    Returns:
        Updated session
    """
    manager = _get_manager()
    
    try:
        session = manager.complete_session(
            session_id=session_id,
            commit_sha=commit_sha,
            pr_url=pr_url
        )
        
        return SessionResponse(
            session=session,
            message=f"Session {session_id} marked as {session.status}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
