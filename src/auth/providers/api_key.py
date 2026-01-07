"""API Key authentication provider."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.auth.models import APIKey


class APIKeyProvider:
    """Provider for API key authentication."""
    
    @staticmethod
    def is_expired(api_key: APIKey) -> bool:
        """
        Check if an API key has expired.
        
        Args:
            api_key: The API key to check
            
        Returns:
            True if the key has expired, False otherwise
        """
        if api_key.expires_at is None:
            return False
        
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        # Ensure expires_at is timezone-aware
        expires_at = api_key.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        return now > expires_at
    
    @staticmethod
    def update_last_used(api_key: APIKey) -> APIKey:
        """
        Update the last_used_at timestamp for an API key.
        
        Args:
            api_key: The API key to update
            
        Returns:
            Updated API key with current timestamp
        """
        api_key.last_used_at = datetime.now(timezone.utc)
        return api_key
