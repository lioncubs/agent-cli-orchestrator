"""Tests for security utilities."""

import pytest
from src.core.security import PasswordHasher, APIKeyHasher, InputValidator


class TestPasswordHasher:
    """Tests for password hashing with bcrypt."""
    
    def test_hash_password(self):
        """Test password hashing."""
        hasher = PasswordHasher()
        password = "test_password_123"
        
        hash1 = hasher.hash_password(password)
        hash2 = hasher.hash_password(password)
        
        # Hashes should be different due to different salts
        assert hash1 != hash2
        
        # Both should verify correctly
        assert hasher.verify_password(password, hash1)
        assert hasher.verify_password(password, hash2)
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        hasher = PasswordHasher()
        password = "my_secure_password"
        password_hash = hasher.hash_password(password)
        
        assert hasher.verify_password(password, password_hash) is True
    
    def test_verify_password_failure(self):
        """Test failed password verification."""
        hasher = PasswordHasher()
        password = "correct_password"
        wrong_password = "wrong_password"
        password_hash = hasher.hash_password(password)
        
        assert hasher.verify_password(wrong_password, password_hash) is False
    
    def test_verify_password_invalid_hash(self):
        """Test password verification with invalid hash."""
        hasher = PasswordHasher()
        
        # Invalid hash format
        assert hasher.verify_password("password", "invalid_hash") is False


class TestAPIKeyHasher:
    """Tests for API key hashing with salt."""
    
    def test_generate_key(self):
        """Test API key generation."""
        hasher = APIKeyHasher()
        
        key1 = hasher.generate_key()
        key2 = hasher.generate_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be URL-safe
        assert len(key1) > 0
        assert len(key2) > 0
    
    def test_hash_key(self):
        """Test API key hashing with salt."""
        hasher = APIKeyHasher()
        key = "test_api_key_12345"
        
        hash1 = hasher.hash_key(key)
        hash2 = hasher.hash_key(key)
        
        # Hashes should be different due to different salts
        assert hash1 != hash2
        
        # Both should contain salt separator
        assert "$" in hash1
        assert "$" in hash2
    
    def test_verify_key_success(self):
        """Test successful API key verification."""
        hasher = APIKeyHasher()
        key = "my_api_key_xyz"
        key_hash = hasher.hash_key(key)
        
        assert hasher.verify_key(key, key_hash) is True
    
    def test_verify_key_failure(self):
        """Test failed API key verification."""
        hasher = APIKeyHasher()
        correct_key = "correct_key"
        wrong_key = "wrong_key"
        key_hash = hasher.hash_key(correct_key)
        
        assert hasher.verify_key(wrong_key, key_hash) is False
    
    def test_verify_key_legacy_hash(self):
        """Test verification of legacy hash without salt."""
        hasher = APIKeyHasher()
        import hashlib
        
        # Create a legacy hash (no salt)
        key = "legacy_key"
        legacy_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
        
        # Should still verify for backwards compatibility
        assert hasher.verify_key(key, legacy_hash) is True
    
    def test_verify_key_invalid_hash(self):
        """Test API key verification with invalid hash."""
        hasher = APIKeyHasher()
        
        assert hasher.verify_key("key", "invalid$hash$format") is False


class TestInputValidator:
    """Tests for input validation and sanitization."""
    
    def test_validate_branch_name_valid(self):
        """Test validation of valid branch names."""
        assert InputValidator.validate_branch_name("main") is True
        assert InputValidator.validate_branch_name("feature/new-feature") is True
        assert InputValidator.validate_branch_name("bugfix-123") is True
        assert InputValidator.validate_branch_name("release/v1.0.0") is True
    
    def test_validate_branch_name_invalid(self):
        """Test validation of invalid branch names."""
        assert InputValidator.validate_branch_name("") is False
        assert InputValidator.validate_branch_name("-invalid") is False
        assert InputValidator.validate_branch_name("../etc/passwd") is False
        assert InputValidator.validate_branch_name("branch with spaces") is False
        assert InputValidator.validate_branch_name("a" * 300) is False  # Too long
    
    def test_validate_repo_name_valid(self):
        """Test validation of valid repo names."""
        assert InputValidator.validate_repo_name("my-repo") is True
        assert InputValidator.validate_repo_name("repo_123") is True
        assert InputValidator.validate_repo_name("my.repo") is True
    
    def test_validate_repo_name_invalid(self):
        """Test validation of invalid repo names."""
        assert InputValidator.validate_repo_name("") is False
        assert InputValidator.validate_repo_name("repo/with/slash") is False
        assert InputValidator.validate_repo_name("../parent") is False
        assert InputValidator.validate_repo_name("a" * 300) is False
    
    def test_sanitize_path_valid(self):
        """Test sanitization of valid paths."""
        assert InputValidator.sanitize_path("src/file.py") == "src/file.py"
        assert InputValidator.sanitize_path("docs/readme.md") == "docs/readme.md"
        assert InputValidator.sanitize_path("  path/file.txt  ") == "path/file.txt"
    
    def test_sanitize_path_invalid(self):
        """Test sanitization rejects dangerous paths."""
        with pytest.raises(ValueError):
            InputValidator.sanitize_path("../etc/passwd")
        
        with pytest.raises(ValueError):
            InputValidator.sanitize_path("/absolute/path")
        
        with pytest.raises(ValueError):
            InputValidator.sanitize_path("path/../../../etc")
    
    def test_sanitize_command_arg_valid(self):
        """Test sanitization of valid command arguments."""
        assert InputValidator.sanitize_command_arg("--option") == "--option"
        assert InputValidator.sanitize_command_arg("value123") == "value123"
        assert InputValidator.sanitize_command_arg("file.txt") == "file.txt"
    
    def test_sanitize_command_arg_invalid(self):
        """Test sanitization rejects dangerous command arguments."""
        dangerous_args = [
            "arg; rm -rf /",
            "arg && malicious",
            "arg | other",
            "arg `whoami`",
            "arg $(malicious)",
            "arg <input",
            "arg >output",
        ]
        
        for arg in dangerous_args:
            with pytest.raises(ValueError):
                InputValidator.sanitize_command_arg(arg)
    
    def test_validate_email_valid(self):
        """Test validation of valid email addresses."""
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("test.user@domain.co.uk") is True
        assert InputValidator.validate_email("user+tag@example.com") is True
    
    def test_validate_email_invalid(self):
        """Test validation of invalid email addresses."""
        assert InputValidator.validate_email("") is False
        assert InputValidator.validate_email("notanemail") is False
        assert InputValidator.validate_email("@example.com") is False
        assert InputValidator.validate_email("user@") is False
        assert InputValidator.validate_email("a" * 300 + "@example.com") is False
    
    def test_validate_uuid_valid(self):
        """Test validation of valid UUIDs."""
        assert InputValidator.validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True
        assert InputValidator.validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
    
    def test_validate_uuid_invalid(self):
        """Test validation of invalid UUIDs."""
        assert InputValidator.validate_uuid("") is False
        assert InputValidator.validate_uuid("not-a-uuid") is False
        assert InputValidator.validate_uuid("123e4567-e89b-12d3-a456") is False  # Too short
        assert InputValidator.validate_uuid("123e4567-e89b-12d3-a456-426614174000-extra") is False
