"""Query and research MCP tools."""

from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from src.mcp.models import (
    QueryInput,
    StartResearchInput,
    CompleteResearchInput,
    TurnResult,
    SessionResult,
    ResearchArtifactResult,
    MCPError
)
from src.query.service import QueryService
from src.query.research_service import ResearchService
from src.session.store import SessionStore
from src.session.models import SessionType, SessionStatus
from src.registry.research_store import ResearchStore


class QueryTools:
    """MCP tools for query and research operations."""
    
    def __init__(
        self,
        query_service: QueryService,
        research_service: ResearchService,
        session_store: SessionStore,
        research_store: ResearchStore
    ):
        """
        Initialize query tools.
        
        Args:
            query_service: Query execution service
            research_service: Research service
            session_store: Session storage
            research_store: Research artifact storage
        """
        self.query_service = query_service
        self.research_service = research_service
        self.session_store = session_store
        self.research_store = research_store
    
    async def query(self, input_data: QueryInput) -> Dict[str, Any]:
        """
        Execute a read-only query on a repository.
        
        Args:
            input_data: Query input parameters
            
        Returns:
            TurnResult with query response
        """
        try:
            result = await self.query_service.execute_query(
                repo_name=input_data.repo_name,
                prompt=input_data.prompt,
                session_id=input_data.session_id
            )
            
            return TurnResult(
                turn_id=result.get("turn_id", 1),
                prompt=input_data.prompt,
                response=result.get("response", ""),
                response_summary=result.get("response_summary", ""),
                files_analyzed=result.get("files_analyzed", []),
                files_changed=result.get("files_changed", []),
                timestamp=datetime.now()
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Query execution failed",
                details=str(e)
            ).model_dump()
    
    async def start_research(self, input_data: StartResearchInput) -> Dict[str, Any]:
        """
        Start a research session with temporary worktree.
        
        Args:
            input_data: Research session parameters
            
        Returns:
            SessionResult for the new research session
        """
        try:
            session = await self.research_service.start_research(
                repo_name=input_data.repo_name,
                prompt=input_data.prompt,
                base_branch=input_data.base_branch
            )
            
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
                files_changed=session.files_changed
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to start research session",
                details=str(e)
            ).model_dump()
    
    async def complete_research(self, input_data: CompleteResearchInput) -> Dict[str, Any]:
        """
        Complete a research session and generate artifact.
        
        Args:
            input_data: Research completion parameters
            
        Returns:
            ResearchArtifactResult with findings and recommendations
        """
        try:
            # Get the session
            session = await self.session_store.get_session(input_data.session_id)
            
            if not session:
                return MCPError(
                    error="Session not found",
                    session_id=input_data.session_id
                ).model_dump()
            
            if session.type != SessionType.RESEARCH:
                return MCPError(
                    error="Session is not a research session",
                    session_id=input_data.session_id
                ).model_dump()
            
            # Complete research and generate artifact
            artifact = await self.research_service.complete_research(input_data.session_id)
            
            return ResearchArtifactResult(
                research_id=artifact.research_id,
                repo_name=artifact.repo_name,
                base_branch=artifact.base_branch,
                base_commit=artifact.base_commit,
                created_at=artifact.created_at,
                user_id=artifact.user_id,
                summary=artifact.summary,
                findings=artifact.findings,
                recommendations=artifact.recommendations,
                conversation=artifact.conversation,
                suggested_delegation_prompt=artifact.suggested_delegation_prompt,
                relevant_files=artifact.relevant_files
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to complete research",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
