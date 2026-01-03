"""
Executor - Step Execution Engine
Orchestrates tool execution with error handling, timeouts, and context management
"""
from typing import Any, Dict, Optional
import time
from datetime import datetime

from app.schemas.plan_schema import StepSchema
from app.schemas.tool_schema import ToolInput, ToolResult
from app.schemas.state_schema import AgentState
from app.schemas.execution_schema import ExecutionLog, RetryContext, ErrorContext
from app.utils.logger import get_logger
from app.config import config

logger = get_logger("agent.executor")


class Executor:
    """
    Executes plan steps using tools
    Features:
    - Dynamic tool selection
    - Timeout handling
    - Context passing between steps
    - Progress tracking
    - Rollback mechanisms
    """
    
    def __init__(self):
        self.logger = logger
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Initialize available tools
        TODO: Load from tool registry in Phase 3
        """
        # Placeholder: Return empty dict
        # In Phase 3, this will load actual tool instances
        return {
            "email_tool": None,
            "calendar_tool": None,
            "web_search_tool": None,
            "file_tool": None
        }
    
    def execute_step(
        self,
        step: StepSchema,
        state: AgentState,
        retry_context: Optional[RetryContext] = None
    ) -> ToolResult:
        """
        Execute a single step
        
        Args:
            step: Step to execute
            state: Current agent state
            retry_context: Retry history (if retrying)
            
        Returns:
            ToolResult with execution outcome
        """
        attempt_number = (retry_context.total_attempts + 1) if retry_context else 1
        
        self.logger.info(
            "Executing step",
            step_id=step.id,
            action=step.action,
            tool=step.tool,
            attempt=attempt_number
        )
        
        # Create execution log
        exec_log = ExecutionLog(
            step_id=step.id,
            attempt_number=attempt_number,
            status="started",
            tool_name=step.tool
        )
        
        start_time = time.time()
        
        try:
            # Resolve step parameters (handle ${step_X.output} references)
            resolved_params = self._resolve_parameters(step.params, state)
            exec_log.tool_input = resolved_params
            exec_log.add_log(f"Resolved parameters: {resolved_params}")
            
            # Get the tool
            tool = self._get_tool(step.tool)
            if not tool:
                raise ValueError(f"Tool '{step.tool}' not available")
            
            # Create tool input
            tool_input = ToolInput(
                action=step.action,
                params=resolved_params,
                context=self._build_execution_context(step, state),
                timeout_seconds=step.timeout_seconds,
                retry_on_failure=True
            )
            
            exec_log.add_log("Calling tool")
            
            # Execute tool with timeout
            result = self._execute_with_timeout(
                tool=tool,
                tool_input=tool_input,
                timeout=step.timeout_seconds
            )
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            # Update execution log
            exec_log.mark_completed(
                success=result.success,
                output=result.data,
                error=result.error
            )
            
            if result.success:
                self.logger.info(
                    "Step executed successfully",
                    step_id=step.id,
                    duration_ms=duration_ms
                )
                state.add_action(f"✓ {step.action} completed")
            else:
                self.logger.error(
                    "Step execution failed",
                    step_id=step.id,
                    error=result.error,
                    duration_ms=duration_ms
                )
            
            # Add execution log to result metadata
            result.add_metadata("execution_log", exec_log.model_dump())
            
            return result
            
        except TimeoutError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Step timed out after {step.timeout_seconds}s"
            
            self.logger.error(
                "Step timeout",
                step_id=step.id,
                timeout=step.timeout_seconds
            )
            
            exec_log.mark_completed(success=False, error=error_msg)
            exec_log.status = "timeout"
            
            return ToolResult(
                success=False,
                error=error_msg,
                error_type="timeout",
                duration_ms=duration_ms,
                metadata={"execution_log": exec_log.model_dump()}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.logger.error(
                "Step execution error",
                step_id=step.id,
                error=error_msg,
                exc_info=True
            )
            
            exec_log.mark_completed(success=False, error=error_msg)
            exec_log.stack_trace = str(e)
            
            return ToolResult(
                success=False,
                error=error_msg,
                error_type="internal_error",
                duration_ms=duration_ms,
                metadata={"execution_log": exec_log.model_dump()}
            )
    
    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Resolve parameter references like ${step_1.output}
        
        Args:
            params: Raw parameters with potential references
            state: Agent state with previous outputs
            
        Returns:
            Resolved parameters
        """
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference: ${step_1.output} -> step_1, output
                ref = value[2:-1]  # Remove ${ and }
                
                if "." in ref:
                    step_id, field = ref.split(".", 1)
                    
                    # Get output from completed step
                    step_output = state.execution_context.get_step_output(step_id)
                    
                    if step_output:
                        if field == "output":
                            resolved[key] = step_output
                        elif isinstance(step_output, dict) and field in step_output:
                            resolved[key] = step_output[field]
                        else:
                            self.logger.warning(
                                f"Cannot resolve reference: {value}"
                            )
                            resolved[key] = None
                    else:
                        self.logger.warning(
                            f"Step {step_id} output not found"
                        )
                        resolved[key] = None
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _build_execution_context(
        self,
        step: StepSchema,
        state: AgentState
    ) -> Dict[str, Any]:
        """Build context for tool execution"""
        return {
            "step_id": step.id,
            "plan_id": state.plan.id if state.plan else None,
            "user_goal": state.user_goal,
            "previous_steps": state.execution_context.completed_steps,
            "available_outputs": list(state.execution_context.step_outputs.keys())
        }
    
    def _get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get tool instance by name
        TODO: Implement with actual tools in Phase 3
        """
        # Placeholder: Return mock tool
        if tool_name in self.tools:
            # In Phase 3, return actual tool instance
            # For now, return a mock
            return MockTool(tool_name)
        return None
    
    def _execute_with_timeout(
        self,
        tool: Any,
        tool_input: ToolInput,
        timeout: int
    ) -> ToolResult:
        """
        Execute tool with timeout protection
        
        Args:
            tool: Tool instance
            tool_input: Tool input
            timeout: Timeout in seconds
            
        Returns:
            ToolResult
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Execution exceeded {timeout}s timeout")
        
        # Set up timeout (Unix only)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            result = tool.execute(tool_input)
            
            signal.alarm(0)  # Cancel timeout
            return result
            
        except AttributeError:
            # Windows doesn't support signal.SIGALRM
            # Fall back to simple execution
            self.logger.warning("Timeout protection not available on Windows")
            return tool.execute(tool_input)
    
    def execute_multiple_steps(
        self,
        steps: list[StepSchema],
        state: AgentState,
        parallel: bool = False
    ) -> Dict[str, ToolResult]:
        """
        Execute multiple steps
        
        Args:
            steps: Steps to execute
            state: Agent state
            parallel: Whether to execute in parallel (if no dependencies)
            
        Returns:
            Dict mapping step_id to ToolResult
        """
        results = {}
        
        if parallel:
            # TODO: Implement parallel execution
            # For now, execute sequentially
            self.logger.warning("Parallel execution not yet implemented")
        
        for step in steps:
            result = self.execute_step(step, state)
            results[step.id] = result
            
            # Update state with result
            if result.success:
                state.execution_context.mark_step_completed(
                    step.id,
                    result.data
                )
            else:
                state.execution_context.mark_step_failed(
                    step.id,
                    result.error or "Unknown error"
                )
        
        return results
    
    def rollback_step(
        self,
        step: StepSchema,
        state: AgentState
    ) -> bool:
        """
        Attempt to rollback a failed step
        
        Args:
            step: Step to rollback
            state: Agent state
            
        Returns:
            True if rollback successful
        """
        self.logger.info("Attempting rollback", step_id=step.id)
        
        # TODO: Implement rollback logic
        # - Check if step has rollback capability
        # - Execute inverse operation
        # - Update state
        
        self.logger.warning("Rollback not yet implemented")
        return False


class MockTool:
    """
    Mock tool for testing
    TODO: Replace with actual tools in Phase 3
    """
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Mock execution - always succeeds"""
        logger.debug(f"Mock tool '{self.name}' executing action '{tool_input.action}'")
        
        # Simulate some work
        time.sleep(0.1)
        
        # Return mock success
        return ToolResult(
            success=True,
            data={
                "tool": self.name,
                "action": tool_input.action,
                "params": tool_input.params,
                "mock": True,
                "result": "Mock execution successful"
            },
            duration_ms=100.0
        )


# Global executor instance
executor = Executor()


if __name__ == "__main__":
    """Test executor"""
    from app.schemas.plan_schema import PlanSchema
    
    print("⚙️ Testing Executor...")
    
    # Create test step
    step = StepSchema(
        id="step_1",
        action="fetch_emails",
        tool="email_tool",
        params={"days": 7},
        success_criteria="emails retrieved"
    )
    
    # Create test state
    plan = PlanSchema(
        objective="Test",
        steps=[step]
    )
    
    state = AgentState(
        user_goal="Test goal",
        plan=plan,
        status="executing"
    )
    
    # Execute step
    result = executor.execute_step(step, state)
    
    print(f"\n✅ Step executed")
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Data: {result.data}")
    
    print("\n✅ Executor test complete")