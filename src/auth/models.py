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


class CopilotPAT(BaseModel):
    """Copilot Personal Access Token model."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    pat_encrypted: str  # Encrypted with Fernet
    pat_hash: str  # SHA-256 hash for validation
    label: str  # User-defined label (e.g., "Work", "Personal")
    scopes: List[str] = Field(default_factory=lambda: ["copilot"])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    is_active: bool = True
    validation_failures: int = 0
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None


class CopilotPATCreate(BaseModel):
    """Model for creating a new Copilot PAT."""
    pat: str  # Plaintext PAT (will be encrypted)
    label: str
    expires_at: Optional[datetime] = None


class CopilotPATUpdate(BaseModel):
    """Model for updating a Copilot PAT."""
    label: Optional[str] = None
    is_active: Optional[bool] = None


class CopilotPATResponse(BaseModel):
    """Response model for Copilot PAT (excludes sensitive data)."""
    id: UUID
    user_id: UUID
    label: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    last_validated_at: Optional[datetime]
    is_active: bool
    validation_failures: int
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]
