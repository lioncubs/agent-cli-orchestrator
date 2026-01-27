"""Data models for memory system."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class Memory(BaseModel):
    """Represents a single memory entry."""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class MemoryCreateRequest(BaseModel):
    """Request to create a new memory."""
    user_id: str
    content: str
    tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class MemoryUpdateRequest(BaseModel):
    """Request to update an existing memory."""
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class MemoryResponse(BaseModel):
    """Response containing a single memory."""
    memory: Memory
    message: str = "Success"


class MemoryListResponse(BaseModel):
    """Response containing a list of memories."""
    memories: List[Memory]
    total: int
    user_id: str
