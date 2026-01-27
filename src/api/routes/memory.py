"""API routes for memory management."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.memory.models import (
    Memory,
    MemoryCreateRequest,
    MemoryUpdateRequest,
    MemoryResponse,
    MemoryListResponse
)
from src.memory.service import MemoryService


# Initialize router
router = APIRouter(prefix="/memories", tags=["memories"])

# Global instance (to be initialized by main app)
_memory_service: Optional[MemoryService] = None


def init_memory_routes(memory_service: MemoryService):
    """
    Initialize memory routes with service instance.
    
    Args:
        memory_service: Memory service instance
    """
    global _memory_service
    _memory_service = memory_service


class DeleteMemoryResponse(BaseModel):
    """Response for memory deletion."""
    success: bool
    message: str


@router.post("/", response_model=MemoryResponse)
async def create_memory(request: MemoryCreateRequest):
    """
    Create a new memory for a user.
    
    Args:
        request: Memory creation request
        
    Returns:
        Created memory object
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memory = await _memory_service.create_memory(request)
        return MemoryResponse(
            memory=memory,
            message="Memory created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=MemoryListResponse)
async def get_memories(
    user_id: str = Query(..., description="User ID to retrieve memories for"),
    limit: Optional[int] = Query(None, description="Maximum number of memories to return")
):
    """
    Get all memories for a user.
    
    Args:
        user_id: User identifier
        limit: Optional limit on number of memories
        
    Returns:
        List of memories
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memories = await _memory_service.get_memories(user_id, limit=limit)
        return MemoryListResponse(
            memories=memories,
            total=len(memories),
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last", response_model=MemoryResponse)
async def get_last_memory(
    user_id: str = Query(..., description="User ID to retrieve last memory for")
):
    """
    Get the most recently created memory for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Most recent memory
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memory = await _memory_service.get_last_memory(user_id)
        if memory is None:
            raise HTTPException(
                status_code=404, 
                detail=f"No memories found for user {user_id}"
            )
        
        return MemoryResponse(
            memory=memory,
            message="Last memory retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID who owns the memory")
):
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: Memory identifier
        user_id: User identifier
        
    Returns:
        Memory object
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memory = await _memory_service.get_memory(user_id, memory_id)
        if memory is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Memory {memory_id} not found for user {user_id}"
            )
        
        return MemoryResponse(
            memory=memory,
            message="Memory retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    request: MemoryUpdateRequest,
    user_id: str = Query(..., description="User ID who owns the memory")
):
    """
    Update an existing memory.
    
    Args:
        memory_id: Memory identifier
        request: Update request
        user_id: User identifier
        
    Returns:
        Updated memory object
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memory = await _memory_service.update_memory(user_id, memory_id, request)
        if memory is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Memory {memory_id} not found for user {user_id}"
            )
        
        return MemoryResponse(
            memory=memory,
            message="Memory updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}", response_model=DeleteMemoryResponse)
async def delete_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID who owns the memory")
):
    """
    Delete a memory.
    
    Args:
        memory_id: Memory identifier
        user_id: User identifier
        
    Returns:
        Success status
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        success = await _memory_service.delete_memory(user_id, memory_id)
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Memory {memory_id} not found for user {user_id}"
            )
        
        return DeleteMemoryResponse(
            success=True,
            message="Memory deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=MemoryListResponse)
async def search_memories(
    user_id: str = Query(..., description="User ID to search memories for"),
    query: str = Query(..., description="Search query string")
):
    """
    Search memories by content.
    
    Args:
        user_id: User identifier
        query: Search query string
        
    Returns:
        List of matching memories
    """
    if _memory_service is None:
        raise HTTPException(status_code=500, detail="Memory service not initialized")
    
    try:
        memories = await _memory_service.search_memories(user_id, query)
        return MemoryListResponse(
            memories=memories,
            total=len(memories),
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
