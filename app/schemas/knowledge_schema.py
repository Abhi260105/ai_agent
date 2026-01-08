from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class KnowledgeCategory(str, Enum):
    FACT = "fact"
    CONCEPT = "concept"
    PROCEDURE = "procedure"
    RELATION = "relation"
    EVENT = "event"
    ENTITY = "entity"


class ConfidenceLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class KnowledgeSource(str, Enum):
    USER_INPUT = "user_input"
    DOCUMENT = "document"
    WEB_SEARCH = "web_search"
    INFERENCE = "inference"
    EXTERNAL_API = "external_api"


class KnowledgeCreate(BaseModel):
    title: str = Field(..., description="Knowledge item title")
    content: str = Field(..., description="Knowledge content")
    category: KnowledgeCategory = Field(default=KnowledgeCategory.FACT)
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.MEDIUM)
    source: KnowledgeSource = Field(default=KnowledgeSource.USER_INPUT)
    source_url: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)
    relationships: Optional[Dict[str, List[int]]] = Field(default_factory=dict)
    verified: bool = Field(default=False)


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    confidence: Optional[ConfidenceLevel] = None
    source: Optional[KnowledgeSource] = None
    source_url: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    relationships: Optional[Dict[str, List[int]]] = None
    verified: Optional[bool] = None
    access_count: Optional[int] = None
    last_accessed: Optional[datetime] = None


class KnowledgeResponse(BaseModel):
    id: int
    title: str
    content: str
    category: KnowledgeCategory
    confidence: ConfidenceLevel
    source: KnowledgeSource
    source_url: Optional[str] = None
    embedding_id: Optional[str] = None
    metadata: Dict[str, Any]
    tags: List[str]
    relationships: Dict[str, List[int]]
    verified: bool
    access_count: int
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime]

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    category: Optional[KnowledgeCategory] = None
    confidence: Optional[ConfidenceLevel] = None
    source: Optional[KnowledgeSource] = None
    tags: Optional[List[str]] = None
    verified_only: bool = Field(default=False)
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    knowledge_items: List[KnowledgeResponse]
    total_count: int
    query: str
    filters_applied: Dict[str, Any]


class KnowledgeGraphNode(BaseModel):
    id: int
    title: str
    category: KnowledgeCategory
    importance: float = Field(default=1.0)


class KnowledgeGraphEdge(BaseModel):
    source_id: int
    target_id: int
    relationship_type: str
    weight: float = Field(default=1.0)


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]
    center_node_id: Optional[int] = None
    depth: int = Field(default=1)


class KnowledgeRelationRequest(BaseModel):
    source_id: int
    target_id: int
    relationship_type: str = Field(..., description="Type: related_to, causes, part_of, instance_of, etc.")
    bidirectional: bool = Field(default=False)


class KnowledgeStats(BaseModel):
    total_knowledge: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    by_confidence: Dict[str, int]
    verified_count: int
    avg_confidence: float
    most_connected: Optional[KnowledgeResponse] = None
    recently_added: List[KnowledgeResponse] = Field(default_factory=list)


class KnowledgeExportRequest(BaseModel):
    format: str = Field(default="json", description="Export format: json, csv, markdown")
    category: Optional[KnowledgeCategory] = None
    tags: Optional[List[str]] = None
    verified_only: bool = Field(default=False)


class KnowledgeImportRequest(BaseModel):
    format: str = Field(default="json", description="Import format: json, csv, markdown")
    data: str = Field(..., description="Data to import")
    merge_strategy: str = Field(default="skip", description="Strategy: skip, replace, merge")