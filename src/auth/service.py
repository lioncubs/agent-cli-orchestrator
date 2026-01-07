"""Authentication service."""

import hashlib
from typing import Optional
from uuid import UUID

from src.auth.models import User, UserCreate, APIKey, APIKeyCreate
from src.auth.providers.api_key import APIKeyProvider
from src.session.models import GitIdentity
from src.storage.base import StorageBackend


class AuthService:
    """Service for authentication and authorization operations."""
    
    def __init__(self, storage: StorageBackend):
        """
        Initialize authentication service.
        
        Args:
            storage: Storage backend for persisting users and API keys
        """
        self.storage = storage
        self.api_key_provider = APIKeyProvider()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using SHA-256.
        
        Args:
            password: The plaintext password
            
        Returns:
            SHA-256 hash of the password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: The plaintext password
            password_hash: The stored hash to verify against
            
        Returns:
            True if the password matches the hash, False otherwise
        """
        return AuthService.hash_password(password) == password_hash
    
    async def create_user(self, user_create: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            Created user
            
        Raises:
            ValueError: If a user with the same email already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_create.email)
        if existing_user:
            raise ValueError(f"User with email {user_create.email} already exists")
        
        # Create git identity
        git_identity = GitIdentity(
            name=user_create.git_name,
            email=user_create.git_email
        )
        
        # Create user
        user = User(
            email=user_create.email,
            display_name=user_create.display_name,
            password_hash=self.hash_password(user_create.password),
            git_identity=git_identity,
            default_model=user_create.default_model,
            permission_tier=user_create.permission_tier
        )
        
        # Store user
        await self.storage.set(f"users/{user.id}", user.model_dump())
        await self.storage.set(f"users/by_email/{user.email}", str(user.id))
        
        return user
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        data = await self.storage.get(f"users/{user_id}")
        if not data:
            return None
        
        return User(**data)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        user_id_str = await self.storage.get(f"users/by_email/{email}")
        if not user_id_str:
            return None
        
        return await self.get_user(UUID(user_id_str))
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User if authentication succeeds, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create_api_key(
        self,
        user_id: UUID,
        api_key_create: APIKeyCreate
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            api_key_create: API key creation data
            
        Returns:
            Tuple of (APIKey model, plaintext key)
            Note: The plaintext key is only returned once and should be given to the user
        """
        # Generate plaintext key
        plaintext_key = self.api_key_provider.generate_key()
        
        # Create API key
        api_key = APIKey(
            key_hash=self.api_key_provider.hash_key(plaintext_key),
            user_id=user_id,
            name=api_key_create.name,
            scopes=api_key_create.scopes,
            expires_at=api_key_create.expires_at
        )
        
        # Store API key
        await self.storage.set(f"api_keys/{api_key.id}", api_key.model_dump())
        
        # Index by user
        user_keys = await self.storage.get(f"api_keys/by_user/{user_id}")
        if user_keys is None:
            user_keys = []
        user_keys.append(str(api_key.id))
        await self.storage.set(f"api_keys/by_user/{user_id}", user_keys)
        
        return api_key, plaintext_key
    
    async def get_api_key(self, api_key_id: UUID) -> Optional[APIKey]:
        """
        Get an API key by ID.
        
        Args:
            api_key_id: API key ID
            
        Returns:
            APIKey if found, None otherwise
        """
        data = await self.storage.get(f"api_keys/{api_key_id}")
        if not data:
            return None
        
        return APIKey(**data)
    
    async def list_user_api_keys(self, user_id: UUID) -> list[APIKey]:
        """
        List all API keys for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of API keys
        """
        user_keys = await self.storage.get(f"api_keys/by_user/{user_id}")
        if not user_keys:
            return []
        
        api_keys = []
        for key_id in user_keys:
            api_key = await self.get_api_key(UUID(key_id))
            if api_key:
                api_keys.append(api_key)
        
        return api_keys
    
    async def authenticate_api_key(self, key: str) -> Optional[tuple[User, APIKey]]:
        """
        Authenticate using an API key.
        
        Args:
            key: The plaintext API key
            
        Returns:
            Tuple of (User, APIKey) if authentication succeeds, None otherwise
        """
        # Search all API keys (in production, use a hash index)
        all_keys = await self.storage.list("api_keys/")
        
        for key_path in all_keys:
            # Skip index entries
            if "/by_user/" in key_path:
                continue
            
            data = await self.storage.get(key_path)
            if not data:
                continue
            
            api_key = APIKey(**data)
            
            # Verify key
            if not self.api_key_provider.verify_key(key, api_key.key_hash):
                continue
            
            # Check expiration
            if self.api_key_provider.is_expired(api_key):
                continue
            
            # Update last used
            api_key = self.api_key_provider.update_last_used(api_key)
            await self.storage.set(f"api_keys/{api_key.id}", api_key.model_dump())
            
            # Get user
            user = await self.get_user(api_key.user_id)
            if not user:
                continue
            
            return user, api_key
        
        return None
    
    async def revoke_api_key(self, api_key_id: UUID) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key_id: API key ID
            
        Returns:
            True if the key was revoked, False if it didn't exist
        """
        # Get the API key to find the user
        api_key = await self.get_api_key(api_key_id)
        if not api_key:
            return False
        
        # Remove from user's key list
        user_keys = await self.storage.get(f"api_keys/by_user/{api_key.user_id}")
        if user_keys and str(api_key_id) in user_keys:
            user_keys.remove(str(api_key_id))
            await self.storage.set(f"api_keys/by_user/{api_key.user_id}", user_keys)
        
        # Delete the API key
        return await self.storage.delete(f"api_keys/{api_key_id}")
    
    async def update_user(self, user_id: UUID, **updates) -> Optional[User]:
        """
        Update user fields.
        
        Args:
            user_id: User ID
            **updates: Fields to update
            
        Returns:
            Updated user if found, None otherwise
        """
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        # Update timestamp
        from datetime import datetime
        user.updated_at = datetime.utcnow()
        
        # Store updated user
        await self.storage.set(f"users/{user.id}", user.model_dump())
        
        return user
