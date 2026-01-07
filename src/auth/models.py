"""Authentication models."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr

from src.session.models import GitIdentity


class User(BaseModel):
    """User model for authentication and authorization."""
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    display_name: str
    password_hash: str
    git_identity: GitIdentity
    default_model: str = "gpt-4o"
    permission_tier: str = "restricted"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    """Model for creating a new user."""
    email: EmailStr
    display_name: str
    password: str
    git_name: str
    git_email: EmailStr
    default_model: str = "gpt-4o"
    permission_tier: str = "restricted"


class APIKey(BaseModel):
    """API key model for authentication."""
    id: UUID = Field(default_factory=uuid4)
    key_hash: str  # Salted SHA-256 hash, never store plaintext
    user_id: UUID
    name: str
    scopes: List[str] = Field(default_factory=list)  # ["read", "write", "admin"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    """Model for creating a new API key."""
    name: str
    scopes: List[str] = Field(default_factory=lambda: ["read", "write"])
    expires_at: Optional[datetime] = None
