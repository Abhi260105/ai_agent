"""
Graph Schema Definitions
Models for LangGraph state machine and node execution
"""
from typing import Any, Dict, List, Optional, Literal, Callable
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.state_schema import AgentState
from app.schemas.plan_schema import StepSchema


class NodeOutput(BaseModel):
    """
    Output from a graph node execution
    Standard return format for all nodes
    """
    
    updated_state: AgentState = Field(
        ...,
        description="Updated agent state after node execution"
    )
    
    next_node: Optional[str] = Field(
        default=None,
        description="Explicit next node to execute (overrides routing)"
    )
    
    should_end: bool = Field(
        default=False,
        description="Whether to end graph execution"
    )
    
    node_name: str = Field(
        ...,
        description="Name of the node that produced this output"
    )
    
    execution_time_ms: float = Field(
        default=0.0,
        description="Time taken to execute node"
    )
    
    logs: List[str] = Field(
        default_factory=list,
        description="Log messages from node execution"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def add_log(self, message: str):
        """Add a log message"""
        self.logs.append(f"[{datetime.now().isoformat()}] {message}")


class EdgeCondition(BaseModel):
    """
    Condition for routing between nodes
    Used in conditional edges
    """
    
    condition_name: str = Field(
        ...,
        description="Name of the condition"
    )
    
    source_node: str = Field(
        ...,
        description="Node this edge originates from"
    )
    
    target_node: str = Field(
        ...,
        description="Node this edge leads to"
    )
    
    condition_function: Optional[Callable] = Field(
        default=None,
        description="Function that evaluates the condition"
    )
    
    priority: int = Field(
        default=0,
        description="Priority when multiple conditions match"
    )
    
    description: str = Field(
        default="",
        description="Human-readable description"
    )
    
    class Config:
        arbitrary_types_allowed = True


class CheckpointData(BaseModel):
    """
    State checkpoint for persistence
    Allows resuming execution from any point
    """
    
    checkpoint_id: str = Field(
        default_factory=lambda: f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        description="Unique checkpoint identifier"
    )
    
    state: AgentState = Field(
        ...,
        description="Agent state at checkpoint"
    )
    
    node_name: str = Field(
        ...,
        description="Current node when checkpoint was created"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When checkpoint was created"
    )
    
    can_resume: bool = Field(
        default=True,
        description="Whether execution can resume from this checkpoint"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional checkpoint metadata"
    )


class GraphState(BaseModel):
    """
    Complete graph execution state
    Extends AgentState with graph-specific information
    """
    
    agent_state: AgentState = Field(
        ...,
        description="Core agent state"
    )
    
    current_node: str = Field(
        default="start",
        description="Currently executing node"
    )
    
    visited_nodes: List[str] = Field(
        default_factory=list,
        description="Nodes that have been executed"
    )
    
    node_outputs: Dict[str, NodeOutput] = Field(
        default_factory=dict,
        description="Outputs from each node execution"
    )
    
    cycle_count: int = Field(
        default=0,
        description="Number of times graph has cycled"
    )
    
    max_cycles: int = Field(
        default=10,
        description="Maximum allowed cycles before aborting"
    )
    
    checkpoints: List[CheckpointData] = Field(
        default_factory=list,
        description="State checkpoints for recovery"
    )
    
    graph_started_at: datetime = Field(
        default_factory=datetime.now,
        description="When graph execution started"
    )
    
    graph_ended_at: Optional[datetime] = Field(
        default=None,
        description="When graph execution ended"
    )
    
    def add_visited_node(self, node_name: str):
        """Mark node as visited"""
        self.visited_nodes.append(node_name)
        self.current_node = node_name
    
    def has_visited(self, node_name: str) -> bool:
        """Check if node has been visited"""
        return node_name in self.visited_nodes
    
    def increment_cycle(self) -> bool:
        """
        Increment cycle count
        Returns True if max cycles exceeded
        """
        self.cycle_count += 1
        return self.cycle_count > self.max_cycles
    
    def create_checkpoint(self) -> CheckpointData:
        """Create checkpoint at current state"""
        checkpoint = CheckpointData(
            state=self.agent_state,
            node_name=self.current_node
        )
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def get_latest_checkpoint(self) -> Optional[CheckpointData]:
        """Get most recent checkpoint"""
        return self.checkpoints[-1] if self.checkpoints else None


class GraphExecutionResult(BaseModel):
    """
    Result of complete graph execution
    """
    
    final_state: AgentState = Field(
        ...,
        description="Final agent state"
    )
    
    status: Literal["success", "failed", "aborted", "timeout"] = Field(
        ...,
        description="Execution status"
    )
    
    nodes_executed: List[str] = Field(
        default_factory=list,
        description="Nodes that were executed"
    )
    
    total_cycles: int = Field(
        default=0,
        description="Total graph cycles"
    )
    
    execution_time_seconds: float = Field(
        default=0.0,
        description="Total execution time"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    checkpoints_created: int = Field(
        default=0,
        description="Number of checkpoints created"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata"
    )


class GraphMetrics(BaseModel):
    """
    Metrics about graph execution
    Used for monitoring and optimization
    """
    
    total_executions: int = Field(
        default=0,
        description="Total graph executions"
    )
    
    successful_executions: int = Field(
        default=0,
        description="Successful executions"
    )
    
    failed_executions: int = Field(
        default=0,
        description="Failed executions"
    )
    
    average_execution_time_seconds: float = Field(
        default=0.0,
        description="Average execution time"
    )
    
    average_cycles: float = Field(
        default=0.0,
        description="Average number of cycles"
    )
    
    node_execution_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="How many times each node was executed"
    )
    
    node_failure_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="How many times each node failed"
    )
    
    most_common_paths: List[List[str]] = Field(
        default_factory=list,
        description="Most frequently taken execution paths"
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100


class NodeConfig(BaseModel):
    """
    Configuration for a graph node
    """
    
    name: str = Field(
        ...,
        description="Node name (must be unique)"
    )
    
    description: str = Field(
        default="",
        description="Node description"
    )
    
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Node execution timeout"
    )
    
    retryable: bool = Field(
        default=True,
        description="Whether node can be retried"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    
    required: bool = Field(
        default=True,
        description="Whether node must succeed"
    )
    
    can_skip: bool = Field(
        default=False,
        description="Whether node can be skipped"
    )
    
    checkpoint_after: bool = Field(
        default=False,
        description="Create checkpoint after node execution"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )


# Example graph state for testing
EXAMPLE_GRAPH_STATE = GraphState(
    agent_state=AgentState(
        user_goal="Test goal",
        status="initializing"
    ),
    current_node="planner",
    max_cycles=5
)


if __name__ == "__main__":
    """Test graph schemas"""
    
    # Test NodeOutput
    output = NodeOutput(
        updated_state=AgentState(user_goal="test", status="planning"),
        node_name="planner",
        execution_time_ms=123.45
    )
    output.add_log("Planning completed")
    
    print("📊 Node Output:")
    print(f"  Node: {output.node_name}")
    print(f"  Time: {output.execution_time_ms}ms")
    print(f"  Logs: {len(output.logs)}")
    
    # Test GraphState
    graph_state = EXAMPLE_GRAPH_STATE
    graph_state.add_visited_node("planner")
    graph_state.add_visited_node("executor")
    
    print(f"\n🔄 Graph State:")
    print(f"  Current: {graph_state.current_node}")
    print(f"  Visited: {graph_state.visited_nodes}")
    print(f"  Cycles: {graph_state.cycle_count}/{graph_state.max_cycles}")
    
    # Test checkpoint
    checkpoint = graph_state.create_checkpoint()
    print(f"\n💾 Checkpoint:")
    print(f"  ID: {checkpoint.checkpoint_id}")
    print(f"  Node: {checkpoint.node_name}")
    
    print("\n✅ Graph schema tests complete")