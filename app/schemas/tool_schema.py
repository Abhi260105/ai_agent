"""
Tool Schema Definitions
Defines input/output structures for all tools
"""
from typing import Any, Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """
    Standard input format for all tools
    Ensures consistent tool invocation
    """
    
    action: str = Field(
        ...,
        description="Action to perform (tool-specific)"
    )
    
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Action parameters"
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context (e.g., previous step outputs)"
    )
    
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Maximum execution time"
    )
    
    retry_on_failure: bool = Field(
        default=True,
        description="Whether to retry on failure"
    )


class ToolResult(BaseModel):
    """
    Standard output format for all tools
    Enforces structured error handling
    """
    
    success: bool = Field(
        ...,
        description="Whether execution succeeded"
    )
    
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool output data"
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    error_type: Optional[str] = Field(
        default=None,
        description="Error category (network, auth, validation, etc.)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata"
    )
    
    executed_at: datetime = Field(
        default_factory=datetime.now,
        description="Execution timestamp"
    )
    
    duration_ms: float = Field(
        default=0.0,
        description="Execution time in milliseconds"
    )
    
    retries: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    
    @property
    def is_success(self) -> bool:
        """Alias for success field"""
        return self.success
    
    @property
    def has_error(self) -> bool:
        """Check if result contains an error"""
        return not self.success and self.error is not None
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata entry"""
        self.metadata[key] = value


class EmailToolInput(ToolInput):
    """Specialized input for email tool"""
    pass


class EmailToolResult(ToolResult):
    """Specialized result for email tool with typed data"""
    
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "emails": [],
            "count": 0,
            "unread_count": 0
        }
    )


class CalendarToolInput(ToolInput):
    """Specialized input for calendar tool"""
    pass


class CalendarToolResult(ToolResult):
    """Specialized result for calendar tool with typed data"""
    
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "events": [],
            "conflicts": [],
            "scheduled": []
        }
    )


class WebSearchToolInput(ToolInput):
    """Specialized input for web search tool"""
    pass


class WebSearchToolResult(ToolResult):
    """Specialized result for web search tool with typed data"""
    
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "results": [],
            "total_results": 0,
            "search_query": ""
        }
    )


class FileToolInput(ToolInput):
    """Specialized input for file tool"""
    pass


class FileToolResult(ToolResult):
    """Specialized result for file tool with typed data"""
    
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "file_path": "",
            "operation": "",
            "size_bytes": 0
        }
    )


class ToolCapability(BaseModel):
    """
    Describes a tool's capabilities
    Used for tool discovery and validation
    """
    
    name: str = Field(..., description="Tool name")
    
    description: str = Field(..., description="Tool description")
    
    supported_actions: List[str] = Field(
        ...,
        description="List of actions this tool can perform"
    )
    
    required_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Required parameters for each action"
    )
    
    optional_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional parameters for each action"
    )
    
    requires_auth: bool = Field(
        default=False,
        description="Whether tool requires authentication"
    )
    
    rate_limit: Optional[int] = Field(
        default=None,
        description="Max calls per minute (if applicable)"
    )
    
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Example usage cases"
    )


class ToolExecutionLog(BaseModel):
    """
    Log entry for tool execution
    Used for debugging and monitoring
    """
    
    tool_name: str = Field(..., description="Tool that was executed")
    
    action: str = Field(..., description="Action performed")
    
    input_params: Dict[str, Any] = Field(
        ...,
        description="Input parameters (may be sanitized)"
    )
    
    result: ToolResult = Field(..., description="Execution result")
    
    step_id: Optional[str] = Field(
        default=None,
        description="Associated step ID"
    )
    
    plan_id: Optional[str] = Field(
        default=None,
        description="Associated plan ID"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When execution occurred"
    )


class ToolRegistry(BaseModel):
    """
    Registry of available tools
    Maintains tool capabilities and metadata
    """
    
    tools: Dict[str, ToolCapability] = Field(
        default_factory=dict,
        description="Registered tools"
    )
    
    def register(self, capability: ToolCapability):
        """Register a new tool"""
        self.tools[capability.name] = capability
    
    def get(self, name: str) -> Optional[ToolCapability]:
        """Get tool capability by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())
    
    def supports_action(self, tool_name: str, action: str) -> bool:
        """Check if tool supports a specific action"""
        tool = self.get(tool_name)
        if not tool:
            return False
        return action in tool.supported_actions


class ToolUsageMetrics(BaseModel):
    """
    Metrics for tool usage tracking
    Used by learning engine
    """
    
    tool_name: str = Field(..., description="Tool name")
    
    total_calls: int = Field(default=0, description="Total number of calls")
    
    successful_calls: int = Field(default=0, description="Successful calls")
    
    failed_calls: int = Field(default=0, description="Failed calls")
    
    avg_duration_ms: float = Field(default=0.0, description="Average execution time")
    
    total_duration_ms: float = Field(default=0.0, description="Total execution time")
    
    error_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of each error type"
    )
    
    last_used: Optional[datetime] = Field(
        default=None,
        description="Last time tool was used"
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100
    
    def update(self, result: ToolResult):
        """Update metrics with new result"""
        self.total_calls += 1
        
        if result.success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            if result.error_type:
                self.error_types[result.error_type] = \
                    self.error_types.get(result.error_type, 0) + 1
        
        self.total_duration_ms += result.duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_calls
        self.last_used = datetime.now()


class ToolError(BaseModel):
    """
    Standardized tool error
    Used for consistent error reporting
    """
    
    tool_name: str = Field(..., description="Tool that failed")
    
    action: str = Field(..., description="Action that was attempted")
    
    error_type: str = Field(..., description="Error category")
    
    error_message: str = Field(..., description="Human-readable error")
    
    technical_details: Optional[str] = Field(
        default=None,
        description="Technical error details"
    )
    
    stack_trace: Optional[str] = Field(
        default=None,
        description="Full stack trace"
    )
    
    recoverable: bool = Field(
        default=True,
        description="Whether error is recoverable"
    )
    
    retry_recommended: bool = Field(
        default=False,
        description="Whether retry is recommended"
    )
    
    occurred_at: datetime = Field(
        default_factory=datetime.now,
        description="When error occurred"
    )


# Example tool capabilities
EMAIL_TOOL_CAPABILITY = ToolCapability(
    name="email_tool",
    description="Read and parse emails from Gmail",
    supported_actions=["fetch", "search", "get_thread", "mark_read", "send"],
    required_params={
        "fetch": "days: int",
        "search": "query: str",
        "get_thread": "thread_id: str",
        "send": "to: str, subject: str, body: str"
    },
    optional_params={
        "fetch": "filter: str, max_results: int",
        "search": "max_results: int",
        "send": "cc: str, bcc: str"
    },
    requires_auth=True,
    rate_limit=100,
    examples=[
        {
            "action": "fetch",
            "params": {"days": 7, "filter": "unread"},
            "description": "Fetch unread emails from last 7 days"
        },
        {
            "action": "send",
            "params": {
                "to": "team@example.com",
                "subject": "Meeting Update",
                "body": "The meeting has been rescheduled."
            },
            "description": "Send email to team"
        }
    ]
)

CALENDAR_TOOL_CAPABILITY = ToolCapability(
    name="calendar_tool",
    description="Manage Google Calendar events",
    supported_actions=["list_events", "create_event", "update_event", "check_conflicts", "delete_event"],
    required_params={
        "list_events": "start_date: str, end_date: str",
        "create_event": "title: str, start_time: str, end_time: str",
        "delete_event": "event_id: str"
    },
    optional_params={
        "create_event": "attendees: List[str], description: str, location: str",
        "list_events": "max_results: int"
    },
    requires_auth=True,
    rate_limit=50,
    examples=[
        {
            "action": "create_event",
            "params": {
                "title": "Team Meeting",
                "start_time": "2024-03-15T10:00:00",
                "end_time": "2024-03-15T11:00:00",
                "attendees": ["team@example.com"]
            },
            "description": "Schedule a team meeting"
        }
    ]
)


if __name__ == "__main__":
    """Test tool schemas"""
    
    # Test ToolResult creation
    result = ToolResult(
        success=True,
        data={"emails": 5, "unread": 2},
        duration_ms=123.45
    )
    
    print("📊 Tool Result:")
    print(result.model_dump_json(indent=2))
    
    # Test ToolRegistry
    registry = ToolRegistry()
    registry.register(EMAIL_TOOL_CAPABILITY)
    registry.register(CALENDAR_TOOL_CAPABILITY)
    
    print(f"\n✅ Registered tools: {registry.list_tools()}")
    print(f"📧 Email tool supports 'fetch': {registry.supports_action('email_tool', 'fetch')}")
    print(f"📅 Calendar tool supports 'delete': {registry.supports_action('calendar_tool', 'delete_event')}")
    
    # Test ToolUsageMetrics
    metrics = ToolUsageMetrics(tool_name="email_tool")
    metrics.update(result)
    
    print(f"\n📈 Tool Metrics:")
    print(f"   Total calls: {metrics.total_calls}")
    print(f"   Success rate: {metrics.success_rate:.1f}%")
    print(f"   Avg duration: {metrics.avg_duration_ms:.2f}ms")
    
    print("\n✅ Tool schema test complete")