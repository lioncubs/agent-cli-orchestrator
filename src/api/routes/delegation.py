"""API routes for delegation mode operations."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.session.models import Session, SessionType, GitIdentity
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.delegation.service import DelegationService


# Request/Response Models
class CreateDelegationRequest(BaseModel):
    """Request to create a delegation session."""
    repo_name: str
    user_id: str
    user_identity: GitIdentity
    base_branch: str
    task_slug: Optional[str] = None
    ttl_hours: Optional[int] = None


class ContinueDelegationRequest(BaseModel):
    """Request to continue a delegation session."""
    prompt: str
    response: str = ""
    response_summary: Optional[str] = None
    files_analyzed: list[str] = Field(default_factory=list)
    files_changed: list[str] = Field(default_factory=list)


class CommitDelegationRequest(BaseModel):
    """Request to commit delegation changes."""
    message: Optional[str] = None


class CreatePRRequest(BaseModel):
    """Request to create a pull request."""
    title: str
    body: Optional[str] = None
    draft: bool = False


class DelegationResponse(BaseModel):
    """Response containing delegation session data."""
    session: Session
    message: str = "Success"


class DelegationStatusResponse(BaseModel):
    """Response with delegation status."""
    session_id: str
    status: str
    base_branch: Optional[str]
    session_branch: Optional[str]
    worktree_path: Optional[str]
    commit_sha: Optional[str]
    pr_url: Optional[str]
    files_changed: list[str]
    has_uncommitted_changes: bool


# Initialize router
router = APIRouter(prefix="/delegation", tags=["delegation"])

# Global instances (to be initialized by main app)
_session_store: Optional[SessionStore] = None
_session_manager: Optional[SessionManager] = None
_delegation_service: Optional[DelegationService] = None


def init_delegation_routes(
    session_store: SessionStore,
    session_manager: SessionManager,
    delegation_service: DelegationService
):
    """
    Initialize delegation routes with required dependencies.
    
    Args:
        session_store: SessionStore instance
        session_manager: SessionManager instance
        delegation_service: DelegationService instance
    """
    global _session_store, _session_manager, _delegation_service
    _session_store = session_store
    _session_manager = session_manager
    _delegation_service = delegation_service


def _get_service() -> DelegationService:
    """Get the delegation service instance."""
    if _delegation_service is None:
        raise HTTPException(
            status_code=500,
            detail="Delegation service not initialized"
        )
    return _delegation_service


def _get_manager() -> SessionManager:
    """Get the session manager instance."""
    if _session_manager is None:
        raise HTTPException(
            status_code=500,
            detail="Session manager not initialized"
        )
    return _session_manager


@router.post("/sessions", response_model=DelegationResponse, status_code=201)
async def create_delegation_session(request: CreateDelegationRequest):
    """
    Create a new delegation session.
    
    Creates a session, initializes worktree and branch for isolated work.
    
    Args:
        request: Delegation session creation request
        
    Returns:
        Created and initialized delegation session
    """
    manager = _get_manager()
    service = _get_service()
    
    try:
        # Create session
        session = manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name=request.repo_name,
            user_id=request.user_id,
            user_identity=request.user_identity,
            base_branch=request.base_branch,
            ttl_hours=request.ttl_hours
        )
        
        # Initialize delegation (create worktree and branch)
        session = service.initialize_delegation(
            session=session,
            task_slug=request.task_slug
        )
        
        return DelegationResponse(
            session=session,
            message=f"Delegation session {session.id} created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/sessions/{session_id}/continue", response_model=DelegationResponse)
async def continue_delegation(session_id: UUID, request: ContinueDelegationRequest):
    """
    Continue a delegation session with a new turn.
    
    Args:
        session_id: Session UUID
        request: Continue delegation request
        
    Returns:
        Updated session
    """
    manager = _get_manager()
    
    try:
        # Use response_summary or truncate prompt
        response_summary = request.response_summary or request.prompt[:200]
        
        session = manager.continue_session(
            session_id=session_id,
            prompt=request.prompt,
            response=request.response,
            response_summary=response_summary,
            files_analyzed=request.files_analyzed,
            files_changed=request.files_changed
        )
        
        return DelegationResponse(
            session=session,
            message=f"Delegation session {session_id} continued"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/commit", response_model=DelegationResponse)
async def commit_delegation(session_id: UUID, request: CommitDelegationRequest):
    """
    Commit changes in delegation session.
    
    Commits all changes in the session's worktree with proper author/committer identity.
    
    Args:
        session_id: Session UUID
        request: Commit request with optional message
        
    Returns:
        Updated session with commit information
    """
    manager = _get_manager()
    service = _get_service()
    
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Commit changes
        session = service.commit_changes(
            session=session,
            message=request.message
        )
        
        if session.commit_sha:
            message = f"Changes committed: {session.commit_sha[:8]}"
        else:
            message = "No changes to commit"
        
        return DelegationResponse(
            session=session,
            message=message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/pr", response_model=DelegationResponse)
async def create_delegation_pr(session_id: UUID, request: CreatePRRequest):
    """
    Create a pull request for delegation session.
    
    Creates a PR from the session's branch to the base branch.
    
    Args:
        session_id: Session UUID
        request: PR creation request
        
    Returns:
        Updated session with PR information
    """
    manager = _get_manager()
    service = _get_service()
    
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Create pull request
        session = service.create_pull_request(
            session=session,
            title=request.title,
            body=request.body,
            draft=request.draft
        )
        
        return DelegationResponse(
            session=session,
            message=f"Pull request created: {session.pr_url}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", response_model=DelegationResponse)
async def abandon_delegation(
    session_id: UUID,
    delete_branch: bool = Query(True, description="Delete the branch when abandoning")
):
    """
    Abandon delegation session and clean up.
    
    Removes worktree and optionally deletes the branch.
    
    Args:
        session_id: Session UUID
        delete_branch: Whether to delete the branch
        
    Returns:
        Updated session marked as abandoned
    """
    manager = _get_manager()
    service = _get_service()
    
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Abandon delegation
        session = service.abandon_delegation(
            session=session,
            delete_branch=delete_branch
        )
        
        return DelegationResponse(
            session=session,
            message=f"Delegation session {session_id} abandoned"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/status", response_model=DelegationStatusResponse)
async def get_delegation_status(session_id: UUID):
    """
    Get detailed status of delegation session.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Delegation status information
    """
    manager = _get_manager()
    service = _get_service()
    
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        status = service.get_delegation_status(session)
        
        return DelegationStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
