"""Tests for API key provider."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.auth.providers.api_key import APIKeyProvider
from src.auth.models import APIKey
from src.core.security import APIKeyHasher


class TestAPIKeyProvider:
    """Test API key provider."""
    
    def test_generate_key(self):
        """Test API key generation."""
        hasher = APIKeyHasher()
        key1 = hasher.generate_key()
        key2 = hasher.generate_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be non-empty strings
        assert isinstance(key1, str)
        assert len(key1) > 0
        assert isinstance(key2, str)
        assert len(key2) > 0
    
    def test_hash_key(self):
        """Test key hashing."""
        hasher = APIKeyHasher()
        key = "test_api_key_12345"
        hash1 = hasher.hash_key(key)
        hash2 = hasher.hash_key(key)
        
        # Same key should produce same hash (salted, so different each time)
        # Actually with salted hashes, they will be different
        # But we can verify both hashes verify against the key
        assert hasher.verify_key(key, hash1) is True
        assert hasher.verify_key(key, hash2) is True
        
        # Hash should be different from key
        assert hash1 != key
        assert hash2 != key
    
    def test_hash_different_keys(self):
        """Test that different keys produce different hashes."""
        hasher = APIKeyHasher()
        key1 = "test_key_1"
        key2 = "test_key_2"
        
        hash1 = hasher.hash_key(key1)
        hash2 = hasher.hash_key(key2)
        
        # Different keys should not verify against each other's hashes
        assert hasher.verify_key(key1, hash2) is False
        assert hasher.verify_key(key2, hash1) is False
    
    def test_verify_key_success(self):
        """Test successful key verification."""
        hasher = APIKeyHasher()
        key = "test_api_key"
        key_hash = hasher.hash_key(key)
        
        assert hasher.verify_key(key, key_hash) is True
    
    def test_verify_key_failure(self):
        """Test failed key verification."""
        hasher = APIKeyHasher()
        key = "test_api_key"
        wrong_key = "wrong_api_key"
        key_hash = hasher.hash_key(key)
        
        assert hasher.verify_key(wrong_key, key_hash) is False
    
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
        before = datetime.now(timezone.utc)
        updated_key = APIKeyProvider.update_last_used(api_key)
        after = datetime.now(timezone.utc)
        
        # Check that last_used_at is set and reasonable
        assert updated_key.last_used_at is not None
        assert before <= updated_key.last_used_at <= after
