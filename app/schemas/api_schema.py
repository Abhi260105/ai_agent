"""
API Schema Models - Request/Response models for REST API
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Task-related models
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskRequest(BaseModel):
    """Request model for task creation."""
    description: str = Field(..., description="Task description", min_length=1)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    use_memory: bool = Field(default=True, description="Use memory context")
    use_tools: bool = Field(default=True, description="Enable tools")
    max_iterations: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=60, ge=1, le=3600, description="Timeout in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class TaskResponse(BaseModel):
    """Response model for task data."""
    id: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    progress: int = Field(ge=0, le=100)
    result: Optional[str] = None
    error: Optional[str] = None
    steps_completed: int = Field(default=0)
    total_steps: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any]
    tags: List[str]

    class Config:
        from_attributes = True


# Memory-related models
class MemoryQuery(BaseModel):
    """Model for memory search queries."""
    query: str = Field(..., min_length=1)
    memory_type: Optional[str] = None
    importance: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata: bool = Field(default=True)


class MemoryQueryResponse(BaseModel):
    """Response for memory queries."""
    query: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    filters_applied: Dict[str, Any]


# Tool-related models
class ToolInvocation(BaseModel):
    """Model for tool invocation requests."""
    tool_name: str = Field(..., description="Name of tool to invoke")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)


class ToolInvocationResult(BaseModel):
    """Result of tool invocation."""
    tool_name: str
    status: str
    result: Any
    error: Optional[str] = None
    duration_ms: float
    timestamp: datetime
    retry_count: int = Field(default=0)


# Admin-related models
class AdminAction(BaseModel):
    """Model for admin actions."""
    action: str = Field(..., description="Action to perform")
    target: Optional[str] = Field(None, description="Target of action")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = Field(None, description="Reason for action")
    force: bool = Field(default=False, description="Force action execution")


class AdminActionResult(BaseModel):
    """Result of admin action."""
    action: str
    target: Optional[str]
    status: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


# Analytics models
class AnalyticsQuery(BaseModel):
    """Query for analytics data."""
    metric: str = Field(..., description="Metric to query")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    granularity: str = Field(default="day", description="hour, day, week, month")
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregation: str = Field(default="sum", description="sum, avg, min, max, count")


class AnalyticsResponse(BaseModel):
    """Response for analytics queries."""
    metric: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]
    period: Dict[str, datetime]
    query_time_ms: float


# Batch operation models
class BatchTaskRequest(BaseModel):
    """Request for batch task creation."""
    tasks: List[TaskRequest]
    execute_parallel: bool = Field(default=True)
    max_parallel: int = Field(default=5, ge=1, le=20)
    stop_on_error: bool = Field(default=False)


class BatchTaskResponse(BaseModel):
    """Response for batch task operations."""
    batch_id: str
    total_tasks: int
    successful: int
    failed: int
    pending: int
    task_ids: List[str]
    errors: List[Dict[str, str]] = Field(default_factory=list)
    created_at: datetime


# Configuration models
class APIConfiguration(BaseModel):
    """API configuration settings."""
    rate_limit_per_minute: int = Field(default=100, ge=1)
    rate_limit_burst: int = Field(default=150, ge=1)
    max_concurrent_tasks: int = Field(default=10, ge=1, le=100)
    default_timeout: int = Field(default=60, ge=1, le=3600)
    enable_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300, ge=0)
    log_level: str = Field(default="INFO")


# Health check models
class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    services: Dict[str, str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-08T10:00:00Z",
                "version": "1.0.0",
                "uptime_seconds": 86400,
                "services": {
                    "database": "operational",
                    "cache": "operational",
                    "queue": "operational"
                }
            }
        }


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    status_code: int
    timestamp: datetime
    path: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Pagination models
class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool