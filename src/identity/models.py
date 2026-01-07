"""Identity models for Git credentials and configuration."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class GitCredential(BaseModel):
    """Git credential for authentication with remote repositories."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    name: str  # Friendly name for the credential
    credential_type: str  # "ssh_key", "https_token", "oauth"
    
    # Encrypted credential data
    encrypted_value: str
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Git remote configuration
    remote_url: Optional[str] = None  # e.g., "https://github.com/user/repo.git"
    remote_name: Optional[str] = "origin"  # Default to "origin"
