"""Data models for session management."""

from enum import Enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SessionType(str, Enum):
    """Type of session."""
    QUERY = "query"
    RESEARCH = "research"
    DELEGATION = "delegation"


class SessionStatus(str, Enum):
    """Status of a session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    COMMITTED = "committed"
    PR_CREATED = "pr_created"
    MERGED = "merged"
    ABANDONED = "abandoned"
    CLOSED = "closed"


class GitIdentity(BaseModel):
    """Git user identity information."""
    name: str
    email: str


class Turn(BaseModel):
    """Represents a single turn (prompt/response pair) in a session."""
    id: int
    prompt: str
    response: str
    response_summary: str
    files_analyzed: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    timestamp: datetime


class TurnSummary(BaseModel):
    """Summarized version of a Turn for research artifacts."""
    id: int
    prompt: str
    response_summary: str
    files_analyzed: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    timestamp: datetime


class Session(BaseModel):
    """Represents a user session with the orchestrator."""
    id: UUID
    type: SessionType
    status: SessionStatus
    repo_name: str
    user_id: str
    user_identity: Optional[GitIdentity] = None
    created_at: datetime
    last_activity_at: datetime
    expires_at: Optional[datetime] = None

    # Copilot session tracking
    copilot_session_id: Optional[str] = None

    # Research/Delegation fields
    base_branch: Optional[str] = None
    base_commit: Optional[str] = None
    session_branch: Optional[str] = None
    worktree_path: Optional[str] = None
    is_temporary: bool = False

    # Conversation
    turns: List[Turn] = Field(default_factory=list)

    # Delegation results
    commit_sha: Optional[str] = None
    files_changed: List[str] = Field(default_factory=list)
    pr_url: Optional[str] = None


class ResearchFinding(BaseModel):
    """Individual finding from research."""
    file: str
    lines: Optional[str] = None
    note: str
    code_snippet: Optional[str] = None


class ResearchArtifact(BaseModel):
    """Research artifact capturing findings and recommendations."""
    research_id: UUID
    repo_name: str
    base_branch: str
    base_commit: str
    created_at: datetime
    user_id: str

    # Summary of research findings
    summary: str
    findings: List[ResearchFinding]
    recommendations: List[str]

    # History of conversations
    conversation: List[TurnSummary]

    # Suggestions for next steps
    suggested_delegation_prompt: str
    relevant_files: List[str]
