"""Pydantic models for MCP tool inputs and outputs."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from src.session.models import SessionType, SessionStatus, GitIdentity, TurnSummary, ResearchFinding


# Query Tool Models
class QueryInput(BaseModel):
    """Input for query tool."""
    repo_name: str = Field(..., description="Repository name")
    prompt: str = Field(..., description="Query prompt")
    session_id: Optional[UUID] = Field(None, description="Optional session ID to continue")


class StartResearchInput(BaseModel):
    """Input for start_research tool."""
    repo_name: str = Field(..., description="Repository name")
    prompt: str = Field(..., description="Research prompt")
    base_branch: Optional[str] = Field(None, description="Base branch for research")


class CompleteResearchInput(BaseModel):
    """Input for complete_research tool."""
    session_id: UUID = Field(..., description="Research session ID")


class TurnResult(BaseModel):
    """Output for a single turn execution."""
    turn_id: int
    prompt: str
    response: str
    response_summary: str
    files_analyzed: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    timestamp: datetime


class SessionResult(BaseModel):
    """Output for session-related operations."""
    session_id: UUID
    type: SessionType
    status: SessionStatus
    repo_name: str
    user_id: str
    created_at: datetime
    last_activity_at: datetime
    base_branch: Optional[str] = None
    session_branch: Optional[str] = None
    worktree_path: Optional[str] = None
    turns_count: int
    files_changed: List[str] = Field(default_factory=list)
    pr_url: Optional[str] = None


class ResearchArtifactResult(BaseModel):
    """Output for complete_research tool."""
    research_id: UUID
    repo_name: str
    base_branch: str
    base_commit: str
    created_at: datetime
    user_id: str
    summary: str
    findings: List[ResearchFinding]
    recommendations: List[str]
    conversation: List[TurnSummary]
    suggested_delegation_prompt: str
    relevant_files: List[str]


# Session Tool Models
class ContinueSessionInput(BaseModel):
    """Input for continue_session tool."""
    session_id: UUID = Field(..., description="Session ID")
    prompt: str = Field(..., description="Follow-up prompt")


class ListSessionsInput(BaseModel):
    """Input for list_sessions tool."""
    type: Optional[SessionType] = Field(None, description="Filter by session type")
    status: Optional[SessionStatus] = Field(None, description="Filter by status")
    repo_name: Optional[str] = Field(None, description="Filter by repository")
    user_id: Optional[str] = Field(None, description="Filter by user")
    limit: int = Field(10, description="Maximum number of sessions to return")


class GetSessionInput(BaseModel):
    """Input for get_session tool."""
    session_id: UUID = Field(..., description="Session ID")


class CloseSessionInput(BaseModel):
    """Input for close_session tool."""
    session_id: UUID = Field(..., description="Session ID")
    abandon: bool = Field(False, description="Mark as abandoned instead of completed")


# Delegation Tool Models
class StartDelegationInput(BaseModel):
    """Input for start_delegation tool."""
    repo_name: str = Field(..., description="Repository name")
    prompt: str = Field(..., description="Delegation task description")
    base_branch: Optional[str] = Field(None, description="Base branch for delegation")
    research_id: Optional[UUID] = Field(None, description="Research ID to base delegation on")
    user_id: str = Field(..., description="User ID")
    user_identity: GitIdentity = Field(..., description="User git identity")
    task_slug: Optional[str] = Field(None, description="Short task identifier")


class CommitChangesInput(BaseModel):
    """Input for commit_changes tool."""
    session_id: UUID = Field(..., description="Delegation session ID")
    message: Optional[str] = Field(None, description="Custom commit message")


class CreatePRInput(BaseModel):
    """Input for create_pr tool."""
    session_id: UUID = Field(..., description="Delegation session ID")
    title: Optional[str] = Field(None, description="Pull request title")
    body: Optional[str] = Field(None, description="Pull request body")
    draft: bool = Field(False, description="Create as draft PR")


class CommitResult(BaseModel):
    """Output for commit_changes tool."""
    session_id: UUID
    commit_sha: str
    files_changed: List[str]
    commit_message: str
    author: GitIdentity
    committer: GitIdentity
    timestamp: datetime


class PRResult(BaseModel):
    """Output for create_pr tool."""
    session_id: UUID
    pr_url: str
    pr_number: Optional[int] = None
    title: str
    body: str
    draft: bool
    head_branch: str
    base_branch: str


# Repository Tool Models
class ListReposInput(BaseModel):
    """Input for list_repos tool."""
    pass  # No parameters needed


class GetRepoInput(BaseModel):
    """Input for get_repo tool."""
    repo_name: str = Field(..., description="Repository name")


class RepoInfo(BaseModel):
    """Information about a repository."""
    name: str
    path: str
    current_branch: Optional[str] = None
    default_branch: Optional[str] = None
    remote_url: Optional[str] = None
    has_uncommitted_changes: bool = False
    active_sessions_count: int = 0


# Error Models
class MCPError(BaseModel):
    """Error response from MCP tools."""
    error: str
    details: Optional[str] = None
    session_id: Optional[UUID] = None
