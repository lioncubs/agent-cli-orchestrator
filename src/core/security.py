"""Security utilities for password hashing, input validation, and sanitization."""

import bcrypt
import hashlib
import secrets
import re
from typing import Optional


class PasswordHasher:
    """Secure password hashing using bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with salt.
        
        Args:
            password: The plaintext password
            
        Returns:
            Bcrypt hash of the password (includes salt)
        """
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its bcrypt hash.
        
        Args:
            password: The plaintext password
            password_hash: The stored bcrypt hash
            
        Returns:
            True if the password matches the hash, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ValueError, AttributeError):
            return False


class APIKeyHasher:
    """Secure API key hashing with salt."""
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a secure random API key.
        
        Returns:
            URL-safe base64 encoded random key (32 bytes)
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_key(key: str) -> str:
        """
        Hash an API key using SHA-256 with salt.
        
        Args:
            key: The plaintext API key
            
        Returns:
            Salted hash in format: salt$hash
        """
        # Generate random salt
        salt = secrets.token_hex(16)
        
        # Hash key with salt
        key_with_salt = f"{salt}{key}"
        key_hash = hashlib.sha256(key_with_salt.encode('utf-8')).hexdigest()
        
        # Return in format: salt$hash
        return f"{salt}${key_hash}"
    
    @staticmethod
    def verify_key(key: str, stored_hash: str) -> bool:
        """
        Verify an API key against its stored hash.
        
        Args:
            key: The plaintext API key
            stored_hash: The stored hash in format: salt$hash
            
        Returns:
            True if the key matches the hash, False otherwise
        """
        try:
            # Split salt and hash
            if '$' not in stored_hash:
                # Legacy hash without salt (for backwards compatibility)
                return hashlib.sha256(key.encode('utf-8')).hexdigest() == stored_hash
            
            salt, expected_hash = stored_hash.split('$', 1)
            
            # Hash the provided key with the stored salt
            key_with_salt = f"{salt}{key}"
            key_hash = hashlib.sha256(key_with_salt.encode('utf-8')).hexdigest()
            
            # Constant-time comparison to prevent timing attacks
            return secrets.compare_digest(key_hash, expected_hash)
        except (ValueError, AttributeError):
            return False


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Pattern for safe branch names (alphanumeric, dash, underscore, slash)
    BRANCH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9/_.-]+$')
    
    # Pattern for safe file paths (no directory traversal)
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9/_.-]+$')
    
    @staticmethod
    def validate_branch_name(branch_name: str) -> bool:
        """
        Validate a Git branch name.
        
        Args:
            branch_name: The branch name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not branch_name or len(branch_name) > 255:
            return False
        
        # Check for dangerous patterns
        if branch_name.startswith('-') or '..' in branch_name:
            return False
        
        return bool(InputValidator.BRANCH_NAME_PATTERN.match(branch_name))
    
    @staticmethod
    def validate_repo_name(repo_name: str) -> bool:
        """
        Validate a repository name.
        
        Args:
            repo_name: The repository name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not repo_name or len(repo_name) > 255:
            return False
        
        # Allow alphanumeric, dash, underscore, and dots
        return bool(re.match(r'^[a-zA-Z0-9_.-]+$', repo_name))
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Sanitize a file path to prevent directory traversal.
        
        Args:
            path: The path to sanitize
            
        Returns:
            Sanitized path
            
        Raises:
            ValueError: If path contains dangerous patterns
        """
        # Remove any leading/trailing whitespace
        path = path.strip()
        
        # Check for directory traversal attempts
        if '..' in path or path.startswith('/'):
            raise ValueError("Path contains invalid characters")
        
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Remove any duplicate slashes
        while '//' in path:
            path = path.replace('//', '/')
        
        return path
    
    @staticmethod
    def sanitize_command_arg(arg: str) -> str:
        """
        Sanitize a command-line argument.
        
        Args:
            arg: The argument to sanitize
            
        Returns:
            Sanitized argument
            
        Raises:
            ValueError: If argument contains shell metacharacters
        """
        # Check for shell metacharacters
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in arg:
                raise ValueError(f"Argument contains dangerous character: {char}")
        
        return arg
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate an email address format.
        
        Args:
            email: The email to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic email validation pattern
        pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(pattern.match(email)) and len(email) <= 255
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """
        Validate a UUID string.
        
        Args:
            uuid_str: The UUID string to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(pattern.match(uuid_str))
