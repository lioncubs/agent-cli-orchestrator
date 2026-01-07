"""Encryption service for sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using Fernet."""
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            key: Encryption key (base64-encoded). If not provided, 
                 reads from ORCHESTRATOR_ENCRYPTION_KEY environment variable.
                 If that's not set, generates a new key.
        """
        if key:
            self.key = key
        else:
            self.key = os.environ.get("ORCHESTRATOR_ENCRYPTION_KEY")
            if not self.key:
                # Generate a new key if none provided
                self.key = Fernet.generate_key().decode()
        
        # Ensure key is bytes for Fernet
        key_bytes = self.key.encode() if isinstance(self.key, str) else self.key
        self.fernet = Fernet(key_bytes)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.
        
        Args:
            data: The plaintext string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not data:
            return ""
        
        encrypted_bytes = self.fernet.encrypt(data.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted: The encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        if not encrypted:
            return ""
        
        decrypted_bytes = self.fernet.decrypt(encrypted.encode())
        return decrypted_bytes.decode()
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
