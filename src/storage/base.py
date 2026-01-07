"""Storage backend base interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value if it exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.
        
        Args:
            key: The key to store under
            value: The value to store
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass
    
    @abstractmethod
    async def list(self, prefix: str = "") -> List[str]:
        """
        List all keys with the given prefix.
        
        Args:
            prefix: The prefix to filter by (empty string for all keys)
            
        Returns:
            List of keys matching the prefix
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        pass
