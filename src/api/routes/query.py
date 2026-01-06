"""API routes for query and research operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.session.models import ResearchArtifact, SessionType
from src.session.store import SessionStore
from src.session.manager import SessionManager
from src.query.service import QueryService
from src.query.research_service import ResearchService
from src.registry.research_store import ResearchStore
from src.permissions.tool_policy import ToolPolicy


# Request/Response Models
class QueryRequest(BaseModel):
    """Request for quick read-only query."""
    repo_name: str
    operation: str  # "read_file", "list_files", "search_code", "get_branch", "list_branches"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: str


class QueryResponse(BaseModel):
    """Response for query operations."""
    status: str
    result: Dict[str, Any]
    message: Optional[str] = None


class ResearchCompleteRequest(BaseModel):
    """Request to complete a research session."""
    summary: str
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    suggested_delegation_prompt: str = ""
    cleanup_worktree: bool = True


class ResearchArtifactResponse(BaseModel):
    """Response containing research artifact."""
    artifact: ResearchArtifact
    message: str = "Success"


class ResearchListResponse(BaseModel):
    """Response for listing research artifacts."""
    artifacts: List[ResearchArtifact]
    total: int
    limit: Optional[int]
    offset: int


class DelegateFromResearchRequest(BaseModel):
    """Request to delegate work based on research artifact."""
    user_id: str
    custom_prompt: Optional[str] = None


class DeleteResearchResponse(BaseModel):
    """Response for research artifact deletion."""
    success: bool
    message: str


# Initialize router
router = APIRouter(prefix="/query", tags=["query", "research"])

# Global instances (to be initialized by main app)
_query_service: Optional[QueryService] = None
_research_service: Optional[ResearchService] = None
_session_manager: Optional[SessionManager] = None
_research_store: Optional[ResearchStore] = None
_tool_policy: Optional[ToolPolicy] = None


def init_query_routes(
    query_service: QueryService,
    research_service: ResearchService,
    session_manager: SessionManager,
    research_store: ResearchStore,
    tool_policy: ToolPolicy
):
    """
    Initialize query routes with required dependencies.
    
    Args:
        query_service: QueryService instance
        research_service: ResearchService instance
        session_manager: SessionManager instance
        research_store: ResearchStore instance
        tool_policy: ToolPolicy instance
    """
    global _query_service, _research_service, _session_manager, _research_store, _tool_policy
    _query_service = query_service
    _research_service = research_service
    _session_manager = session_manager
    _research_store = research_store
    _tool_policy = tool_policy


def _get_query_service() -> QueryService:
    """Get the query service instance."""
    if _query_service is None:
        raise HTTPException(status_code=500, detail="Query service not initialized")
    return _query_service


def _get_research_service() -> ResearchService:
    """Get the research service instance."""
    if _research_service is None:
        raise HTTPException(status_code=500, detail="Research service not initialized")
    return _research_service


def _get_session_manager() -> SessionManager:
    """Get the session manager instance."""
    if _session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return _session_manager


def _get_research_store() -> ResearchStore:
    """Get the research store instance."""
    if _research_store is None:
        raise HTTPException(status_code=500, detail="Research store not initialized")
    return _research_store


@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a quick read-only query on a repository.
    
    Args:
        request: Query request with operation and parameters
        
    Returns:
        Query results
    """
    service = _get_query_service()
    
    try:
        # Map operation to service method
        operation = request.operation
        params = request.parameters
        
        # Add repo_path to parameters (would need to resolve from repo_name)
        # For now, using repo_name as path (would be resolved in production)
        params["repo_path"] = request.repo_name
        
        if operation == "read_file":
            result = service.read_file(**params)
        elif operation == "list_files":
            result = service.list_files(**params)
        elif operation == "search_code":
            result = service.search_code(**params)
        elif operation == "get_branch":
            result = service.get_branch_info(**params)
        elif operation == "list_branches":
            result = service.list_branches(**params)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown operation: {operation}"
            )
        
        return QueryResponse(
            status=result.get("status", "success"),
            result=result
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/complete", response_model=ResearchArtifactResponse)
async def complete_research_session(
    session_id: UUID,
    request: ResearchCompleteRequest
):
    """
    Complete a research session and generate artifact.
    
    Args:
        session_id: Research session UUID
        request: Research completion request
        
    Returns:
        Generated research artifact
    """
    research_service = _get_research_service()
    session_manager = _get_session_manager()
    
    try:
        # Get the session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        if session.type != SessionType.RESEARCH:
            raise HTTPException(
                status_code=400,
                detail=f"Session {session_id} is not a research session"
            )
        
        # Finalize the research
        result = research_service.finalize_research_session(
            session=session,
            summary=request.summary,
            findings=request.findings,
            recommendations=request.recommendations,
            suggested_delegation_prompt=request.suggested_delegation_prompt,
            cleanup_worktree=request.cleanup_worktree,
            repo_path=session.repo_name  # Would be resolved in production
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to complete research")
            )
        
        # Mark session as completed
        session_manager.complete_session(session_id)
        
        # Get the artifact
        research_id = UUID(result["research_id"])
        artifact = research_service.get_research_artifact(research_id)
        
        if not artifact:
            raise HTTPException(
                status_code=500,
                detail="Artifact created but not found"
            )
        
        return ResearchArtifactResponse(
            artifact=artifact,
            message=f"Research session {session_id} completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research", response_model=ResearchListResponse)
async def list_research_artifacts(
    repo_name: Optional[str] = Query(None, description="Filter by repository"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset")
):
    """
    List all research artifacts with optional filters.
    
    Args:
        repo_name: Optional repository filter
        user_id: Optional user filter
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of research artifacts
    """
    research_store = _get_research_store()
    
    try:
        artifacts = research_store.list(
            repo_name=repo_name,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        total = research_store.count(
            repo_name=repo_name,
            user_id=user_id
        )
        
        return ResearchListResponse(
            artifacts=artifacts,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/{research_id}", response_model=ResearchArtifactResponse)
async def get_research_artifact(research_id: UUID):
    """
    Get a specific research artifact by ID.
    
    Args:
        research_id: Research artifact UUID
        
    Returns:
        Research artifact details
    """
    research_store = _get_research_store()
    
    artifact = research_store.get(research_id)
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Research artifact {research_id} not found"
        )
    
    return ResearchArtifactResponse(artifact=artifact)


@router.post("/research/{research_id}/delegate")
async def delegate_from_research(
    research_id: UUID,
    request: DelegateFromResearchRequest
):
    """
    Create a delegation session based on research artifact.
    
    Args:
        research_id: Research artifact UUID
        request: Delegation request
        
    Returns:
        Created delegation session
    """
    research_store = _get_research_store()
    session_manager = _get_session_manager()
    
    try:
        # Get the research artifact
        artifact = research_store.get(research_id)
        if not artifact:
            raise HTTPException(
                status_code=404,
                detail=f"Research artifact {research_id} not found"
            )
        
        # Use custom prompt or suggested prompt
        delegation_prompt = request.custom_prompt or artifact.suggested_delegation_prompt
        
        # Create a delegation session
        session = session_manager.create_session(
            session_type=SessionType.DELEGATION,
            repo_name=artifact.repo_name,
            user_id=request.user_id,
            base_branch=artifact.base_branch
        )
        
        # Add initial turn with research context
        session = session_manager.continue_session(
            session_id=session.id,
            prompt=delegation_prompt,
            response="",
            response_summary=f"Delegation from research {research_id}"
        )
        
        return {
            "status": "success",
            "session_id": str(session.id),
            "research_id": str(research_id),
            "message": "Delegation session created from research artifact"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/research/{research_id}", response_model=DeleteResearchResponse)
async def delete_research_artifact(research_id: UUID):
    """
    Delete a research artifact.
    
    Args:
        research_id: Research artifact UUID
        
    Returns:
        Deletion result
    """
    research_store = _get_research_store()
    
    try:
        success = research_store.delete(research_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Research artifact {research_id} not found"
            )
        
        return DeleteResearchResponse(
            success=True,
            message=f"Research artifact {research_id} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
