"""
Memory Access API Routes
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
import sys
sys.path.append('..')
from app.schemas.memory_schema import (
    MemoryCreate, MemoryUpdate, MemoryResponse,
    MemorySearchRequest, MemorySearchResponse
)

router = APIRouter()


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(memory: MemoryCreate):
    """
    Create a new memory item.
    
    - **content**: Memory content
    - **memory_type**: Type of memory (short_term, long_term, episodic, semantic)
    - **importance**: Importance level
    """
    return MemoryResponse(
        id=1,
        content=memory.content,
        memory_type=memory.memory_type,
        importance=memory.importance,
        metadata=memory.metadata,
        tags=memory.tags,
        access_count=0,
        created_at=datetime.now(),
        last_accessed=None,
        related_memories=memory.related_memories
    )


@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    memory_type: Optional[str] = None,
    importance: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List memory items with optional filtering.
    """
    memories = [
        MemoryResponse(
            id=i,
            content=f"Sample memory {i}",
            memory_type="semantic",
            importance="medium",
            metadata={},
            tags=[],
            access_count=5,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            related_memories=[]
        )
        for i in range(1, 6)
    ]
    
    return memories[offset:offset + limit]


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: int):
    """Get a specific memory by ID."""
    return MemoryResponse(
        id=memory_id,
        content="Sample memory content",
        memory_type="semantic",
        importance="high",
        metadata={},
        tags=["important"],
        access_count=10,
        created_at=datetime.now(),
        last_accessed=datetime.now(),
        related_memories=[]
    )


@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: int, update: MemoryUpdate):
    """Update a memory item."""
    return MemoryResponse(
        id=memory_id,
        content=update.content or "Updated memory",
        memory_type=update.memory_type or "semantic",
        importance=update.importance or "medium",
        metadata=update.metadata or {},
        tags=update.tags or [],
        access_count=update.access_count or 5,
        created_at=datetime.now(),
        last_accessed=datetime.now(),
        related_memories=[]
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: int):
    """Delete a memory item."""
    return None


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """
    Search memories using semantic search.
    
    - **query**: Search query
    - **memory_type**: Filter by memory type
    - **importance**: Filter by importance
    - **tags**: Filter by tags
    - **limit**: Maximum results
    - **similarity_threshold**: Minimum similarity score
    """
    memories = [
        MemoryResponse(
            id=i,
            content=f"Memory matching: {request.query}",
            memory_type="semantic",
            importance="medium",
            metadata={},
            tags=[],
            access_count=5,
            created_at=datetime.now(),
            last_accessed=None,
            related_memories=[]
        )
        for i in range(1, min(request.limit + 1, 4))
    ]
    
    return MemorySearchResponse(
        memories=memories,
        total_count=len(memories),
        query=request.query
    )


@router.get("/stats")
async def get_memory_stats():
    """Get memory usage statistics."""
    return {
        "total_memories": 247,
        "short_term_count": 45,
        "long_term_count": 123,
        "episodic_count": 34,
        "semantic_count": 45,
        "avg_importance": 2.8,
        "total_access_count": 1234
    }