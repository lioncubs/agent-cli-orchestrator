"""User registry for managing users."""

from typing import List, Optional
from uuid import UUID

from src.auth.models import User, UserCreate
from src.auth.service import AuthService
from src.storage.base import StorageBackend


class UserRegistry:
    """Registry for user CRUD operations."""
    
    def __init__(self, storage: StorageBackend):
        """
        Initialize user registry.
        
        Args:
            storage: Storage backend for persisting users
        """
        self.auth_service = AuthService(storage)
    
    async def create(self, user_create: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            Created user
            
        Raises:
            ValueError: If a user with the same email already exists
        """
        return await self.auth_service.create_user(user_create)
    
    async def get(self, user_id: UUID) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return await self.auth_service.get_user(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        return await self.auth_service.get_user_by_email(email)
    
    async def update(self, user_id: UUID, **updates) -> Optional[User]:
        """
        Update user fields.
        
        Args:
            user_id: User ID
            **updates: Fields to update
            
        Returns:
            Updated user if found, None otherwise
        """
        return await self.auth_service.update_user(user_id, **updates)
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if the user was deleted, False if they didn't exist
        """
        # Note: In a real system, we'd also need to delete all associated
        # API keys, sessions, etc.
        user = await self.get(user_id)
        if not user:
            return False
        
        # Delete user from storage
        deleted = await self.auth_service.storage.delete(f"users/{user_id}")
        
        # Delete email index
        await self.auth_service.storage.delete(f"users/by_email/{user.email}")
        
        return deleted
    
    async def list_all(self) -> List[User]:
        """
        List all users.
        
        Returns:
            List of all users
        """
        users = []
        keys = await self.auth_service.storage.list("users/")
        
        for key in keys:
            # Skip index entries
            if "/by_email/" in key:
                continue
            
            data = await self.auth_service.storage.get(key)
            if data:
                users.append(User(**data))
        
        return users
