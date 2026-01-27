"""Memory service for managing user memories."""

import os
from datetime import datetime, timezone
from typing import List, Optional
from pathlib import Path

from src.memory.models import Memory, MemoryCreateRequest, MemoryUpdateRequest
from src.storage.yaml_backend import YAMLBackend


class MemoryService:
    """Service for managing user memories with persistent storage."""
    
    def __init__(self, storage_dir: str = "./data/memories"):
        """
        Initialize memory service.
        
        Args:
            storage_dir: Directory to store memory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage = YAMLBackend(storage_dir)
    
    def _get_user_key(self, user_id: str) -> str:
        """Generate storage key for a user's memories."""
        return f"user_{user_id}_memories"
    
    async def create_memory(self, request: MemoryCreateRequest) -> Memory:
        """
        Create a new memory for a user.
        
        Args:
            request: Memory creation request
            
        Returns:
            Created memory object
        """
        memory = Memory(
            user_id=request.user_id,
            content=request.content,
            tags=request.tags,
            metadata=request.metadata
        )
        
        # Get existing memories for the user
        user_key = self._get_user_key(request.user_id)
        memories_data = await self.storage.get(user_key) or []
        
        # Append new memory
        memories_data.append(memory.model_dump())
        
        # Save to storage
        await self.storage.set(user_key, memories_data)
        
        return memory
    
    async def get_memories(self, user_id: str, limit: Optional[int] = None) -> List[Memory]:
        """
        Get all memories for a user.
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of memories to return
            
        Returns:
            List of memory objects
        """
        user_key = self._get_user_key(user_id)
        memories_data = await self.storage.get(user_key) or []
        
        # Convert to Memory objects
        memories = [Memory(**m) for m in memories_data]
        
        # Sort by created_at descending (newest first)
        memories.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit if specified
        if limit is not None:
            memories = memories[:limit]
        
        return memories
    
    async def get_memory(self, user_id: str, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.
        
        Args:
            user_id: User identifier
            memory_id: Memory identifier
            
        Returns:
            Memory object if found, None otherwise
        """
        memories = await self.get_memories(user_id)
        
        for memory in memories:
            if memory.id == memory_id:
                return memory
        
        return None
    
    async def update_memory(
        self, 
        user_id: str, 
        memory_id: str, 
        request: MemoryUpdateRequest
    ) -> Optional[Memory]:
        """
        Update an existing memory.
        
        Args:
            user_id: User identifier
            memory_id: Memory identifier
            request: Update request with new values
            
        Returns:
            Updated memory object if found, None otherwise
        """
        user_key = self._get_user_key(user_id)
        memories_data = await self.storage.get(user_key) or []
        
        # Find and update the memory
        updated_memory = None
        for i, memory_dict in enumerate(memories_data):
            if memory_dict["id"] == memory_id:
                # Update fields if provided
                if request.content is not None:
                    memory_dict["content"] = request.content
                if request.tags is not None:
                    memory_dict["tags"] = request.tags
                if request.metadata is not None:
                    memory_dict["metadata"] = request.metadata
                
                # Update timestamp
                memory_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                memories_data[i] = memory_dict
                updated_memory = Memory(**memory_dict)
                break
        
        if updated_memory:
            # Save to storage
            await self.storage.set(user_key, memories_data)
        
        return updated_memory
    
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            user_id: User identifier
            memory_id: Memory identifier
            
        Returns:
            True if memory was deleted, False if not found
        """
        user_key = self._get_user_key(user_id)
        memories_data = await self.storage.get(user_key) or []
        
        # Find and remove the memory
        original_count = len(memories_data)
        memories_data = [m for m in memories_data if m["id"] != memory_id]
        
        if len(memories_data) < original_count:
            # Memory was found and removed
            await self.storage.set(user_key, memories_data)
            return True
        
        return False
    
    async def get_last_memory(self, user_id: str) -> Optional[Memory]:
        """
        Get the most recently created memory for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Most recent memory object if exists, None otherwise
        """
        memories = await self.get_memories(user_id, limit=1)
        return memories[0] if memories else None
    
    async def search_memories(self, user_id: str, query: str) -> List[Memory]:
        """
        Search memories by content.
        
        Args:
            user_id: User identifier
            query: Search query string
            
        Returns:
            List of matching memory objects
        """
        memories = await self.get_memories(user_id)
        
        # Simple case-insensitive search in content
        query_lower = query.lower()
        matching_memories = [
            m for m in memories 
            if query_lower in m.content.lower()
        ]
        
        return matching_memories
