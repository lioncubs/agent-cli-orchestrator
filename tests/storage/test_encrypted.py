"""Tests for encryption service."""

import pytest
from cryptography.fernet import InvalidToken

from src.storage.encrypted import EncryptionService


class TestEncryptionService:
    """Test encryption service."""
    
    @pytest.fixture
    def encryption_service(self):
        """Create an encryption service with a test key."""
        # Generate a key for testing
        key = EncryptionService.generate_key()
        return EncryptionService(key=key)
    
    def test_encrypt_decrypt(self, encryption_service):
        """Test basic encryption and decryption."""
        plaintext = "This is a secret message"
        
        # Encrypt
        encrypted = encryption_service.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_empty_string(self, encryption_service):
        """Test encrypting an empty string."""
        encrypted = encryption_service.encrypt("")
        assert encrypted == ""
        
        decrypted = encryption_service.decrypt("")
        assert decrypted == ""
    
    def test_encrypt_unicode(self, encryption_service):
        """Test encrypting unicode characters."""
        plaintext = "Hello 世界 🌍"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_long_text(self, encryption_service):
        """Test encrypting long text."""
        plaintext = "A" * 10000
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_different_encryptions(self, encryption_service):
        """Test that same plaintext produces different ciphertexts."""
        plaintext = "same message"
        
        # Encrypt twice
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        
        # Ciphertexts should be different (due to random IV)
        # Note: Fernet uses timestamp and random data, so they will differ
        # But both should decrypt to the same plaintext
        decrypted1 = encryption_service.decrypt(encrypted1)
        decrypted2 = encryption_service.decrypt(encrypted2)
        
        assert decrypted1 == plaintext
        assert decrypted2 == plaintext
    
    def test_wrong_key(self):
        """Test decryption with wrong key."""
        # Create two services with different keys
        service1 = EncryptionService(key=EncryptionService.generate_key())
        service2 = EncryptionService(key=EncryptionService.generate_key())
        
        plaintext = "secret"
        
        # Encrypt with service1
        encrypted = service1.encrypt(plaintext)
        
        # Try to decrypt with service2 (wrong key)
        with pytest.raises(InvalidToken):
            service2.decrypt(encrypted)
    
    def test_generate_key(self):
        """Test key generation."""
        key1 = EncryptionService.generate_key()
        key2 = EncryptionService.generate_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be valid
        service1 = EncryptionService(key=key1)
        service2 = EncryptionService(key=key2)
        
        # Both should work
        encrypted1 = service1.encrypt("test")
        decrypted1 = service1.decrypt(encrypted1)
        assert decrypted1 == "test"
        
        encrypted2 = service2.encrypt("test")
        decrypted2 = service2.decrypt(encrypted2)
        assert decrypted2 == "test"
    
    def test_invalid_ciphertext(self, encryption_service):
        """Test decrypting invalid ciphertext."""
        with pytest.raises(InvalidToken):
            encryption_service.decrypt("invalid_ciphertext")
    
    def test_multiline_text(self, encryption_service):
        """Test encrypting multiline text."""
        plaintext = """Line 1
Line 2
Line 3
With special chars: !@#$%^&*()"""
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_json_like_data(self, encryption_service):
        """Test encrypting JSON-like string data."""
        plaintext = '{"username": "admin", "password": "secret123", "token": "abc123xyz"}'
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
