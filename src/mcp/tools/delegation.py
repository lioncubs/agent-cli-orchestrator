"""Delegation MCP tools."""

from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from src.mcp.models import (
    StartDelegationInput,
    CommitChangesInput,
    CreatePRInput,
    SessionResult,
    CommitResult,
    PRResult,
    MCPError
)
from src.delegation.service import DelegationService
from src.session.store import SessionStore
from src.session.models import SessionType


class DelegationTools:
    """MCP tools for delegation operations."""
    
    def __init__(
        self,
        delegation_service: DelegationService,
        session_store: SessionStore
    ):
        """
        Initialize delegation tools.
        
        Args:
            delegation_service: Delegation service
            session_store: Session storage
        """
        self.delegation_service = delegation_service
        self.session_store = session_store
    
    async def start_delegation(self, input_data: StartDelegationInput) -> Dict[str, Any]:
        """
        Start a delegation session.
        
        Args:
            input_data: Delegation parameters
            
        Returns:
            SessionResult for new delegation session
        """
        try:
            session = await self.delegation_service.initialize_delegation(
                repo_name=input_data.repo_name,
                user_id=input_data.user_id,
                user_identity=input_data.user_identity,
                base_branch=input_data.base_branch,
                task_slug=input_data.task_slug
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
                error="Failed to start delegation",
                details=str(e)
            ).model_dump()
    
    async def commit_changes(self, input_data: CommitChangesInput) -> Dict[str, Any]:
        """
        Commit changes in a delegation session.
        
        Args:
            input_data: Commit parameters
            
        Returns:
            CommitResult with commit details
        """
        try:
            session = await self.session_store.get_session(input_data.session_id)
            
            if not session:
                return MCPError(
                    error="Session not found",
                    session_id=input_data.session_id
                ).model_dump()
            
            if session.type != SessionType.DELEGATION:
                return MCPError(
                    error="Session is not a delegation session",
                    session_id=input_data.session_id
                ).model_dump()
            
            result = await self.delegation_service.commit_changes(
                session_id=input_data.session_id,
                message=input_data.message
            )
            
            return CommitResult(
                session_id=input_data.session_id,
                commit_sha=result["commit_sha"],
                files_changed=result["files_changed"],
                commit_message=result["message"],
                author=result["author"],
                committer=result["committer"],
                timestamp=datetime.now()
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to commit changes",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
    
    async def create_pr(self, input_data: CreatePRInput) -> Dict[str, Any]:
        """
        Create a pull request for delegation session.
        
        Args:
            input_data: PR creation parameters
            
        Returns:
            PRResult with PR details
        """
        try:
            session = await self.session_store.get_session(input_data.session_id)
            
            if not session:
                return MCPError(
                    error="Session not found",
                    session_id=input_data.session_id
                ).model_dump()
            
            if session.type != SessionType.DELEGATION:
                return MCPError(
                    error="Session is not a delegation session",
                    session_id=input_data.session_id
                ).model_dump()
            
            # Create PR using delegation service (expects session object)
            updated_session = await self.delegation_service.create_pull_request(
                session=session,
                title=input_data.title or f"[Agent] Delegation from session {str(input_data.session_id)[:8]}",
                body=input_data.body,
                draft=input_data.draft
            )
            
            return PRResult(
                session_id=input_data.session_id,
                pr_url=updated_session.pr_url or "",
                pr_number=None,  # Will be in pr_url if available
                title=input_data.title or "",
                body=input_data.body or "",
                draft=input_data.draft,
                head_branch=updated_session.session_branch or "",
                base_branch=updated_session.base_branch or ""
            ).model_dump()
            
        except Exception as e:
            return MCPError(
                error="Failed to create pull request",
                details=str(e),
                session_id=input_data.session_id
            ).model_dump()
