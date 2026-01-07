"""API Key authentication provider."""

import hashlib
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.auth.models import APIKey


class APIKeyProvider:
    """Provider for API key authentication."""
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new API key.
        
        Returns:
            A secure random API key string
        """
        # Generate a 32-byte (256-bit) random key
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_key(key: str) -> str:
        """
        Hash an API key using SHA-256.
        
        Args:
            key: The plaintext API key
            
        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    @staticmethod
    def verify_key(key: str, key_hash: str) -> bool:
        """
        Verify an API key against its hash.
        
        Args:
            key: The plaintext API key
            key_hash: The stored hash to verify against
            
        Returns:
            True if the key matches the hash, False otherwise
        """
        return APIKeyProvider.hash_key(key) == key_hash
    
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
        
        return datetime.utcnow() > api_key.expires_at
    
    @staticmethod
    def update_last_used(api_key: APIKey) -> APIKey:
        """
        Update the last_used_at timestamp for an API key.
        
        Args:
            api_key: The API key to update
            
        Returns:
            Updated API key with current timestamp
        """
        api_key.last_used_at = datetime.utcnow()
        return api_key
