"""Tests for API key provider."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.auth.providers.api_key import APIKeyProvider
from src.auth.models import APIKey


class TestAPIKeyProvider:
    """Test API key provider."""
    
    def test_generate_key(self):
        """Test API key generation."""
        key1 = APIKeyProvider.generate_key()
        key2 = APIKeyProvider.generate_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be non-empty strings
        assert isinstance(key1, str)
        assert len(key1) > 0
        assert isinstance(key2, str)
        assert len(key2) > 0
    
    def test_hash_key(self):
        """Test key hashing."""
        key = "test_api_key_12345"
        hash1 = APIKeyProvider.hash_key(key)
        hash2 = APIKeyProvider.hash_key(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from key
        assert hash1 != key
        
        # Hash should be a hex string (SHA-256 = 64 chars)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)
    
    def test_hash_different_keys(self):
        """Test that different keys produce different hashes."""
        key1 = "test_key_1"
        key2 = "test_key_2"
        
        hash1 = APIKeyProvider.hash_key(key1)
        hash2 = APIKeyProvider.hash_key(key2)
        
        assert hash1 != hash2
    
    def test_verify_key_success(self):
        """Test successful key verification."""
        key = "test_api_key"
        key_hash = APIKeyProvider.hash_key(key)
        
        assert APIKeyProvider.verify_key(key, key_hash) is True
    
    def test_verify_key_failure(self):
        """Test failed key verification."""
        key = "test_api_key"
        wrong_key = "wrong_api_key"
        key_hash = APIKeyProvider.hash_key(key)
        
        assert APIKeyProvider.verify_key(wrong_key, key_hash) is False
    
    def test_is_expired_no_expiry(self):
        """Test expiration check with no expiry date."""
        api_key = APIKey(
            key_hash="hash",
            user_id=uuid4(),
            name="Test Key",
            scopes=["read"]
        )
        
        assert APIKeyProvider.is_expired(api_key) is False
    
    def test_is_expired_future(self):
        """Test expiration check with future expiry date."""
        api_key = APIKey(
            key_hash="hash",
            user_id=uuid4(),
            name="Test Key",
            scopes=["read"],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert APIKeyProvider.is_expired(api_key) is False
    
    def test_is_expired_past(self):
        """Test expiration check with past expiry date."""
        api_key = APIKey(
            key_hash="hash",
            user_id=uuid4(),
            name="Test Key",
            scopes=["read"],
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        
        assert APIKeyProvider.is_expired(api_key) is True
    
    def test_update_last_used(self):
        """Test updating last used timestamp."""
        api_key = APIKey(
            key_hash="hash",
            user_id=uuid4(),
            name="Test Key",
            scopes=["read"]
        )
        
        # Initially no last_used_at
        assert api_key.last_used_at is None
        
        # Update last used
        before = datetime.utcnow()
        updated_key = APIKeyProvider.update_last_used(api_key)
        after = datetime.utcnow()
        
        # Check that last_used_at is set and reasonable
        assert updated_key.last_used_at is not None
        assert before <= updated_key.last_used_at <= after
