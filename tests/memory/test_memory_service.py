"""Tests for memory service."""

import pytest
import os
import shutil
from pathlib import Path

from src.memory.service import MemoryService
from src.memory.models import MemoryCreateRequest, MemoryUpdateRequest


@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary storage directory for tests."""
    storage_dir = tmp_path / "test_memories"
    storage_dir.mkdir()
    yield str(storage_dir)
    # Cleanup
    if storage_dir.exists():
        shutil.rmtree(storage_dir)


@pytest.fixture
def memory_service(temp_storage_dir):
    """Create a memory service instance for testing."""
    return MemoryService(storage_dir=temp_storage_dir)


@pytest.mark.asyncio
async def test_create_memory(memory_service):
    """Test creating a new memory."""
    request = MemoryCreateRequest(
        user_id="test_user",
        content="This is my first memory",
        tags=["test", "important"],
        metadata={"source": "test"}
    )
    
    memory = await memory_service.create_memory(request)
    
    assert memory.user_id == "test_user"
    assert memory.content == "This is my first memory"
    assert memory.tags == ["test", "important"]
    assert memory.metadata == {"source": "test"}
    assert memory.id is not None
    assert memory.created_at is not None


@pytest.mark.asyncio
async def test_get_memories(memory_service):
    """Test retrieving all memories for a user."""
    # Create multiple memories
    for i in range(3):
        request = MemoryCreateRequest(
            user_id="test_user",
            content=f"Memory {i}",
            tags=[f"tag{i}"]
        )
        await memory_service.create_memory(request)
    
    # Retrieve all memories
    memories = await memory_service.get_memories("test_user")
    
    assert len(memories) == 3
    # Should be sorted by created_at descending (newest first)
    assert memories[0].content == "Memory 2"
    assert memories[1].content == "Memory 1"
    assert memories[2].content == "Memory 0"


@pytest.mark.asyncio
async def test_get_memories_with_limit(memory_service):
    """Test retrieving memories with a limit."""
    # Create multiple memories
    for i in range(5):
        request = MemoryCreateRequest(
            user_id="test_user",
            content=f"Memory {i}"
        )
        await memory_service.create_memory(request)
    
    # Retrieve with limit
    memories = await memory_service.get_memories("test_user", limit=2)
    
    assert len(memories) == 2


@pytest.mark.asyncio
async def test_get_last_memory(memory_service):
    """Test retrieving the last memory."""
    # Create multiple memories
    for i in range(3):
        request = MemoryCreateRequest(
            user_id="test_user",
            content=f"Memory {i}"
        )
        await memory_service.create_memory(request)
    
    # Get last memory
    last_memory = await memory_service.get_last_memory("test_user")
    
    assert last_memory is not None
    assert last_memory.content == "Memory 2"


@pytest.mark.asyncio
async def test_get_last_memory_empty(memory_service):
    """Test retrieving the last memory when none exist."""
    last_memory = await memory_service.get_last_memory("nonexistent_user")
    
    assert last_memory is None


@pytest.mark.asyncio
async def test_get_memory_by_id(memory_service):
    """Test retrieving a specific memory by ID."""
    # Create a memory
    request = MemoryCreateRequest(
        user_id="test_user",
        content="Test memory"
    )
    created_memory = await memory_service.create_memory(request)
    
    # Retrieve by ID
    memory = await memory_service.get_memory("test_user", created_memory.id)
    
    assert memory is not None
    assert memory.id == created_memory.id
    assert memory.content == "Test memory"


@pytest.mark.asyncio
async def test_update_memory(memory_service):
    """Test updating a memory."""
    # Create a memory
    request = MemoryCreateRequest(
        user_id="test_user",
        content="Original content"
    )
    created_memory = await memory_service.create_memory(request)
    
    # Update the memory
    update_request = MemoryUpdateRequest(
        content="Updated content",
        tags=["updated"]
    )
    updated_memory = await memory_service.update_memory(
        "test_user", 
        created_memory.id, 
        update_request
    )
    
    assert updated_memory is not None
    assert updated_memory.content == "Updated content"
    assert updated_memory.tags == ["updated"]


@pytest.mark.asyncio
async def test_delete_memory(memory_service):
    """Test deleting a memory."""
    # Create a memory
    request = MemoryCreateRequest(
        user_id="test_user",
        content="To be deleted"
    )
    created_memory = await memory_service.create_memory(request)
    
    # Delete the memory
    success = await memory_service.delete_memory("test_user", created_memory.id)
    
    assert success is True
    
    # Verify it's deleted
    memory = await memory_service.get_memory("test_user", created_memory.id)
    assert memory is None


@pytest.mark.asyncio
async def test_search_memories(memory_service):
    """Test searching memories by content."""
    # Create memories with different content
    memories_to_create = [
        ("I love Python programming", []),
        ("JavaScript is interesting", []),
        ("Python is great for data science", [])
    ]
    
    for content, tags in memories_to_create:
        request = MemoryCreateRequest(
            user_id="test_user",
            content=content,
            tags=tags
        )
        await memory_service.create_memory(request)
    
    # Search for "Python"
    results = await memory_service.search_memories("test_user", "Python")
    
    assert len(results) == 2
    assert all("python" in m.content.lower() for m in results)


@pytest.mark.asyncio
async def test_multiple_users(memory_service):
    """Test that memories are isolated per user."""
    # Create memories for two different users
    request1 = MemoryCreateRequest(
        user_id="user1",
        content="User 1 memory"
    )
    await memory_service.create_memory(request1)
    
    request2 = MemoryCreateRequest(
        user_id="user2",
        content="User 2 memory"
    )
    await memory_service.create_memory(request2)
    
    # Get memories for each user
    user1_memories = await memory_service.get_memories("user1")
    user2_memories = await memory_service.get_memories("user2")
    
    assert len(user1_memories) == 1
    assert len(user2_memories) == 1
    assert user1_memories[0].content == "User 1 memory"
    assert user2_memories[0].content == "User 2 memory"
