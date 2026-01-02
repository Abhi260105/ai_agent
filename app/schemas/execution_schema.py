"""
Execution Schema Definitions
Models for tracking step execution, retries, errors, and progress
"""
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ExecutionLog(BaseModel):
    """
    Detailed log of a single execution attempt
    Records everything that happened during execution
    """
    
    log_id: str = Field(
        default_factory=lambda: f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        description="Unique log identifier"
    )
    
    step_id: str = Field(
        ...,
        description="Step that was executed"
    )
    
    attempt_number: int = Field(
        default=1,
        ge=1,
        description="Attempt number (1 = first try)"
    )
    
    status: Literal["started", "running", "success", "failed", "timeout", "aborted"] = Field(
        ...,
        description="Execution status"
    )
    
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="When execution started"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When execution completed"
    )
    
    duration_ms: float = Field(
        default=0.0,
        description="Execution duration in milliseconds"
    )
    
    tool_name: str = Field(
        ...,
        description="Tool that was used"
    )
    
    tool_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters to tool"
    )
    
    tool_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Output from tool"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    error_type: Optional[str] = Field(
        default=None,
        description="Error category"
    )
    
    stack_trace: Optional[str] = Field(
        default=None,
        description="Full stack trace if error"
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context"
    )
    
    logs: List[str] = Field(
        default_factory=list,
        description="Log messages during execution"
    )
    
    def mark_completed(self, success: bool, output: Any = None, error: str = None):
        """Mark execution as completed"""
        self.completed_at = datetime.now()
        self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000
        self.status = "success" if success else "failed"
        
        if success:
            self.tool_output = output
        else:
            self.error_message = error
    
    def add_log(self, message: str):
        """Add a log message"""
        timestamp = datetime.now().isoformat()
        self.logs.append(f"[{timestamp}] {message}")


class RetryContext(BaseModel):
    """
    Context for retry attempts
    Tracks retry history and determines next retry strategy
    """
    
    step_id: str = Field(
        ...,
        description="Step being retried"
    )
    
    total_attempts: int = Field(
        default=0,
        ge=0,
        description="Total attempts made"
    )
    
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum allowed attempts"
    )
    
    last_attempt_at: Optional[datetime] = Field(
        default=None,
        description="When last attempt was made"
    )
    
    next_attempt_at: Optional[datetime] = Field(
        default=None,
        description="When next attempt should be made"
    )
    
    backoff_multiplier: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Exponential backoff multiplier"
    )
    
    initial_delay_seconds: float = Field(
        default=1.0,
        ge=0.1,
        description="Initial retry delay"
    )
    
    current_delay_seconds: float = Field(
        default=1.0,
        description="Current retry delay"
    )
    
    retry_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for each retry"
    )
    
    execution_logs: List[ExecutionLog] = Field(
        default_factory=list,
        description="Logs of all attempts"
    )
    
    should_retry: bool = Field(
        default=True,
        description="Whether retry should be attempted"
    )
    
    @property
    def attempts_remaining(self) -> int:
        """Calculate remaining attempts"""
        return max(0, self.max_attempts - self.total_attempts)
    
    @property
    def has_attempts_remaining(self) -> bool:
        """Check if retry attempts remain"""
        return self.attempts_remaining > 0
    
    def record_attempt(self, log: ExecutionLog, reason: str = ""):
        """Record a retry attempt"""
        self.total_attempts += 1
        self.last_attempt_at = datetime.now()
        self.execution_logs.append(log)
        
        if reason:
            self.retry_reasons.append(reason)
        
        # Calculate next retry delay (exponential backoff)
        self.current_delay_seconds = self.initial_delay_seconds * (
            self.backoff_multiplier ** (self.total_attempts - 1)
        )
        
        # Check if should continue retrying
        self.should_retry = self.has_attempts_remaining


class ErrorContext(BaseModel):
    """
    Structured error information
    Provides detailed context about what went wrong
    """
    
    error_id: str = Field(
        default_factory=lambda: f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        description="Unique error identifier"
    )
    
    error_type: Literal[
        "network",
        "authentication",
        "authorization",
        "validation",
        "timeout",
        "rate_limit",
        "resource_not_found",
        "conflict",
        "internal_error",
        "external_api",
        "unknown"
    ] = Field(
        default="unknown",
        description="Error category"
    )
    
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Error severity"
    )
    
    is_recoverable: bool = Field(
        default=True,
        description="Whether error is recoverable"
    )
    
    is_transient: bool = Field(
        default=False,
        description="Whether error is temporary (retry may succeed)"
    )
    
    requires_user_action: bool = Field(
        default=False,
        description="Whether user intervention is needed"
    )
    
    error_message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    technical_details: Optional[str] = Field(
        default=None,
        description="Technical error details"
    )
    
    stack_trace: Optional[str] = Field(
        default=None,
        description="Stack trace"
    )
    
    step_id: Optional[str] = Field(
        default=None,
        description="Step where error occurred"
    )
    
    tool_name: Optional[str] = Field(
        default=None,
        description="Tool that caused error"
    )
    
    occurred_at: datetime = Field(
        default_factory=datetime.now,
        description="When error occurred"
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context"
    )
    
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Suggested remediation actions"
    )
    
    retry_recommended: bool = Field(
        default=True,
        description="Whether retry is recommended"
    )
    
    replan_recommended: bool = Field(
        default=False,
        description="Whether replanning is recommended"
    )


class ProgressReport(BaseModel):
    """
    Real-time progress tracking
    Shows current execution status
    """
    
    report_id: str = Field(
        default_factory=lambda: f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        description="Unique report identifier"
    )
    
    plan_id: str = Field(
        ...,
        description="Plan being executed"
    )
    
    objective: str = Field(
        ...,
        description="Overall objective"
    )
    
    status: Literal[
        "initializing",
        "planning",
        "executing",
        "evaluating",
        "replanning",
        "waiting_for_user",
        "completed",
        "failed",
        "aborted"
    ] = Field(
        ...,
        description="Current execution status"
    )
    
    total_steps: int = Field(
        default=0,
        ge=0,
        description="Total steps in plan"
    )
    
    completed_steps: int = Field(
        default=0,
        ge=0,
        description="Steps completed successfully"
    )
    
    failed_steps: int = Field(
        default=0,
        ge=0,
        description="Steps that failed"
    )
    
    skipped_steps: int = Field(
        default=0,
        ge=0,
        description="Steps that were skipped"
    )
    
    current_step_id: Optional[str] = Field(
        default=None,
        description="Currently executing step"
    )
    
    current_step_description: Optional[str] = Field(
        default=None,
        description="Description of current step"
    )
    
    progress_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall progress percentage"
    )
    
    estimated_time_remaining_seconds: Optional[float] = Field(
        default=None,
        description="Estimated time to completion"
    )
    
    elapsed_time_seconds: float = Field(
        default=0.0,
        description="Time elapsed since start"
    )
    
    actions_taken: List[str] = Field(
        default_factory=list,
        description="Actions completed so far"
    )
    
    recent_logs: List[str] = Field(
        default_factory=list,
        description="Recent log messages"
    )
    
    errors_encountered: int = Field(
        default=0,
        ge=0,
        description="Number of errors encountered"
    )
    
    retries_attempted: int = Field(
        default=0,
        ge=0,
        description="Number of retries attempted"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When report was last updated"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def update_progress(self):
        """Recalculate progress percentage"""
        if self.total_steps > 0:
            completed = self.completed_steps + self.skipped_steps
            self.progress_percentage = (completed / self.total_steps) * 100
        else:
            self.progress_percentage = 0.0
        
        self.updated_at = datetime.now()
    
    def add_action(self, action: str):
        """Add completed action"""
        self.actions_taken.append(action)
        self.update_progress()
    
    def add_log(self, log_message: str, max_logs: int = 10):
        """Add recent log (keep only most recent)"""
        self.recent_logs.append(f"[{datetime.now().isoformat()}] {log_message}")
        if len(self.recent_logs) > max_logs:
            self.recent_logs = self.recent_logs[-max_logs:]
        self.updated_at = datetime.now()


# Example instances for testing
EXAMPLE_EXECUTION_LOG = ExecutionLog(
    step_id="step_1",
    attempt_number=1,
    status="success",
    tool_name="email_tool",
    tool_input={"action": "fetch", "days": 7}
)

EXAMPLE_RETRY_CONTEXT = RetryContext(
    step_id="step_2",
    total_attempts=2,
    max_attempts=3
)

EXAMPLE_ERROR_CONTEXT = ErrorContext(
    error_type="timeout",
    severity="medium",
    is_recoverable=True,
    is_transient=True,
    error_message="Request timed out after 30 seconds",
    retry_recommended=True
)


if __name__ == "__main__":
    """Test execution schemas"""
    
    # Test ExecutionLog
    log = EXAMPLE_EXECUTION_LOG
    log.add_log("Fetching emails...")
    log.mark_completed(True, output={"emails": 5})
    
    print("📝 Execution Log:")
    print(f"  Step: {log.step_id}")
    print(f"  Status: {log.status}")
    print(f"  Duration: {log.duration_ms:.2f}ms")
    print(f"  Logs: {len(log.logs)}")
    
    # Test RetryContext
    retry = EXAMPLE_RETRY_CONTEXT
    print(f"\n🔄 Retry Context:")
    print(f"  Attempts: {retry.total_attempts}/{retry.max_attempts}")
    print(f"  Remaining: {retry.attempts_remaining}")
    print(f"  Current delay: {retry.current_delay_seconds:.1f}s")
    
    # Test ErrorContext
    error = EXAMPLE_ERROR_CONTEXT
    print(f"\n❌ Error Context:")
    print(f"  Type: {error.error_type}")
    print(f"  Severity: {error.severity}")
    print(f"  Recoverable: {error.is_recoverable}")
    print(f"  Retry recommended: {error.retry_recommended}")
    
    # Test ProgressReport
    progress = ProgressReport(
        plan_id="plan_123",
        objective="Test objective",
        status="executing",
        total_steps=5,
        completed_steps=2
    )
    progress.update_progress()
    
    print(f"\n📊 Progress Report:")
    print(f"  Status: {progress.status}")
    print(f"  Progress: {progress.progress_percentage:.1f}%")
    print(f"  Completed: {progress.completed_steps}/{progress.total_steps}")
    
    print("\n✅ Execution schema tests complete")