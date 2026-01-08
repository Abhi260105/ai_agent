from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryCreate(BaseModel):
    content: str = Field(..., description="The memory content")
    memory_type: MemoryType = Field(default=MemoryType.SHORT_TERM)
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    related_memories: Optional[List[int]] = Field(default_factory=list)


class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    importance: Optional[MemoryImportance] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    access_count: Optional[int] = None
    last_accessed: Optional[datetime] = None


class MemoryResponse(BaseModel):
    id: int
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    embedding_id: Optional[str] = None
    metadata: Dict[str, Any]
    tags: List[str]
    access_count: int
    created_at: datetime
    last_accessed: Optional[datetime]
    related_memories: List[int]

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    memory_type: Optional[MemoryType] = None
    importance: Optional[MemoryImportance] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class MemorySearchResponse(BaseModel):
    memories: List[MemoryResponse]
    total_count: int
    query: str


class MemoryConsolidationRequest(BaseModel):
    source_memory_ids: List[int] = Field(..., min_items=2)
    consolidation_strategy: str = Field(default="merge", description="Strategy: merge, summarize, or link")


class MemoryStats(BaseModel):
    total_memories: int
    short_term_count: int
    long_term_count: int
    episodic_count: int
    semantic_count: int
    avg_importance: float
    most_accessed: Optional[MemoryResponse] = None
    recent_memories: List[MemoryResponse] = Field(default_factory=list)