"""Pydantic models for API request/response validation."""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class PromptRequest(BaseModel):
    """Request model for Copilot CLI prompt execution."""
    prompt: str
    options: Optional[Dict[str, Any]] = None
    repo_name: Optional[str] = None
    show_full_output: Optional[bool] = False


class BranchSelectRequest(BaseModel):
    """Request model for branch selection."""
    branch: str
    repo_name: Optional[str] = None


class WorktreeCreateRequest(BaseModel):
    """Request model for worktree creation."""
    path: str
    branch: str
    create_branch: Optional[bool] = False
    repo_name: Optional[str] = None
