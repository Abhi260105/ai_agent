"""
Decision Engine
Determines what action to take based on execution results
Routes between retry, replan, escalate, or abort
"""
from typing import Literal, Optional, Tuple
from datetime import datetime, timedelta

from app.schemas.state_schema import AgentState
from app.schemas.execution_schema import ErrorContext, RetryContext
from app.schemas.plan_schema import StepSchema
from app.utils.logger import get_logger
from app.config import config

logger = get_logger("agent.decision_engine")


class DecisionEngine:
    """
    Makes routing decisions for the agent
    Determines next action based on current state
    """
    
    def __init__(self):
        self.max_retries = config.agent.max_retries
        self.logger = logger
    
    def should_retry(
        self,
        step: StepSchema,
        error: ErrorContext,
        retry_context: RetryContext
    ) -> Tuple[bool, str]:
        """
        Determine if step should be retried
        
        Args:
            step: Step that failed
            error: Error context
            retry_context: Retry history
            
        Returns:
            (should_retry, reason)
        """
        # Check if retries available
        if not retry_context.has_attempts_remaining:
            return False, "Max retries exceeded"
        
        # Check if step allows retry
        if step.failure_action == "abort":
            return False, "Step configured to abort on failure"
        
        if step.failure_action == "skip":
            return False, "Step configured to skip on failure"
        
        # Check if error is recoverable
        if not error.is_recoverable:
            return False, f"Unrecoverable error: {error.error_type}"
        
        # Check if error is transient (network issues, timeouts, rate limits)
        if error.is_transient:
            self.logger.info(
                "Retry recommended: transient error",
                step_id=step.id,
                error_type=error.error_type
            )
            return True, f"Transient error: {error.error_type}"
        
        # Check specific error types
        if error.error_type in ["network", "timeout", "rate_limit"]:
            return True, f"Recoverable error: {error.error_type}"
        
        # Check if error explicitly recommends retry
        if error.retry_recommended:
            return True, "Error analysis recommends retry"
        
        # Default: no retry
        return False, f"Error type '{error.error_type}' not suitable for retry"
    
    def should_replan(
        self,
        state: AgentState,
        error: Optional[ErrorContext] = None
    ) -> Tuple[bool, str]:
        """
        Determine if plan should be regenerated
        
        Args:
            state: Current agent state
            error: Error context (if applicable)
            
        Returns:
            (should_replan, reason)
        """
        # Check if we have a plan
        if not state.plan:
            return True, "No plan exists"
        
        # Check if error recommends replanning
        if error and error.replan_recommended:
            return True, "Error analysis recommends replanning"
        
        # Check if too many failures
        failed_count = len(state.execution_context.failed_steps)
        total_count = len(state.plan.steps)
        
        if failed_count > total_count * 0.5:  # More than 50% failed
            return True, f"High failure rate: {failed_count}/{total_count}"
        
        # Check if context has changed significantly
        # (This would check if relevant memories or state changed)
        
        # Check if plan is stuck (same step failing repeatedly)
        if state.current_step:
            retry_count = state.execution_context.retry_count.get(
                state.current_step.id, 0
            )
            if retry_count >= self.max_retries:
                return True, f"Step {state.current_step.id} exhausted retries"
        
        # Default: no replan needed
        return False, "Current plan is still valid"
    
    def should_escalate(
        self,
        state: AgentState,
        error: Optional[ErrorContext] = None
    ) -> Tuple[bool, str]:
        """
        Determine if human intervention is needed
        
        Args:
            state: Current agent state
            error: Error context (if applicable)
            
        Returns:
            (should_escalate, reason)
        """
        # Check if error requires user action
        if error and error.requires_user_action:
            return True, "Error requires user intervention"
        
        # Check if authentication/authorization failed
        if error and error.error_type in ["authentication", "authorization"]:
            return True, f"Access error: {error.error_type}"
        
        # Check if critical error
        if error and error.severity == "critical":
            return True, "Critical error encountered"
        
        # Check if multiple replanning attempts failed
        # (This would track replanning history)
        
        # Check if user preference requires confirmation
        # (This would check user preferences from memory)
        
        # Default: no escalation needed
        return False, "Agent can handle situation autonomously"
    
    def should_abort(
        self,
        state: AgentState,
        error: Optional[ErrorContext] = None
    ) -> Tuple[bool, str]:
        """
        Determine if execution should be aborted
        
        Args:
            state: Current agent state
            error: Error context (if applicable)
            
        Returns:
            (should_abort, reason)
        """
        # Check for fatal errors
        if error:
            if not error.is_recoverable and error.severity in ["high", "critical"]:
                return True, "Fatal unrecoverable error"
            
            if error.error_type == "internal_error" and error.severity == "critical":
                return True, "Critical internal error"
        
        # Check timeout
        elapsed = state.elapsed_time_seconds
        if elapsed > config.agent.timeout_seconds:
            return True, f"Execution timeout: {elapsed:.0f}s > {config.agent.timeout_seconds}s"
        
        # Check if plan is completely failed
        if state.plan:
            all_failed = all(
                step.id in state.execution_context.failed_steps
                for step in state.plan.steps
            )
            if all_failed:
                return True, "All steps have failed"
        
        # Check if user requested abort
        if not state.should_continue:
            return True, "User requested abort"
        
        # Default: continue execution
        return False, "No abort conditions met"
    
    def route_next_state(
        self,
        state: AgentState,
        error: Optional[ErrorContext] = None,
        retry_context: Optional[RetryContext] = None
    ) -> Literal["retry", "replan", "continue", "escalate", "abort", "complete"]:
        """
        Determine the next state to transition to
        
        Args:
            state: Current agent state
            error: Error context (if step failed)
            retry_context: Retry history (if applicable)
            
        Returns:
            Next state name
        """
        self.logger.debug(
            "Routing decision",
            current_status=state.status,
            has_error=error is not None
        )
        
        # Check for abort conditions first
        should_abort, abort_reason = self.should_abort(state, error)
        if should_abort:
            self.logger.warning("Abort decision", reason=abort_reason)
            return "abort"
        
        # Check if plan is complete
        if state.is_plan_complete() and len(state.execution_context.failed_steps) == 0:
            self.logger.info("Plan completed successfully")
            return "complete"
        
        # If there was an error, evaluate recovery options
        if error:
            # Check escalation first (some errors need user input)
            should_escalate, escalate_reason = self.should_escalate(state, error)
            if should_escalate:
                self.logger.info("Escalation decision", reason=escalate_reason)
                return "escalate"
            
            # Try retry if available
            if retry_context and state.current_step:
                should_retry, retry_reason = self.should_retry(
                    state.current_step,
                    error,
                    retry_context
                )
                if should_retry:
                    self.logger.info("Retry decision", reason=retry_reason)
                    return "retry"
            
            # Consider replanning
            should_replan, replan_reason = self.should_replan(state, error)
            if should_replan:
                self.logger.info("Replan decision", reason=replan_reason)
                return "replan"
            
            # If nothing else, abort
            self.logger.warning("No recovery option available, aborting")
            return "abort"
        
        # No error - continue execution
        if state.status == "planning":
            return "continue"  # Move to execution
        
        if state.status == "executing":
            next_step = state.get_next_executable_step()
            if next_step:
                return "continue"  # Continue with next step
            else:
                return "complete"  # No more steps
        
        if state.status == "evaluating":
            return "continue"  # Move to next decision
        
        # Default: continue
        return "continue"
    
    def calculate_retry_delay(
        self,
        retry_context: RetryContext,
        error: ErrorContext
    ) -> float:
        """
        Calculate optimal retry delay
        
        Args:
            retry_context: Retry history
            error: Error context
            
        Returns:
            Delay in seconds
        """
        base_delay = retry_context.current_delay_seconds
        
        # Adjust based on error type
        if error.error_type == "rate_limit":
            # Longer delay for rate limits
            base_delay *= 2.0
        elif error.error_type == "network":
            # Shorter delay for network issues
            base_delay *= 0.5
        
        # Cap delay at 60 seconds
        return min(base_delay, 60.0)


# Global decision engine instance
decision_engine = DecisionEngine()


if __name__ == "__main__":
    """Test decision engine"""
    from app.schemas.state_schema import AgentState, ExecutionContext
    from app.schemas.plan_schema import PlanSchema, StepSchema
    
    # Create test state
    plan = PlanSchema(
        objective="Test",
        steps=[
            StepSchema(
                id="step_1",
                action="test",
                tool="test_tool",
                success_criteria="done"
            )
        ]
    )
    
    state = AgentState(
        user_goal="Test goal",
        plan=plan,
        status="executing"
    )
    
    # Test retry decision
    error = ErrorContext(
        error_type="network",
        severity="medium",
        is_recoverable=True,
        is_transient=True,
        error_message="Connection failed"
    )
    
    retry_ctx = RetryContext(
        step_id="step_1",
        total_attempts=1,
        max_attempts=3
    )
    
    should_retry, reason = decision_engine.should_retry(
        plan.steps[0],
        error,
        retry_ctx
    )
    
    print("🎯 Decision Engine Test:")
    print(f"  Should retry: {should_retry}")
    print(f"  Reason: {reason}")
    
    # Test routing
    next_state = decision_engine.route_next_state(state, error, retry_ctx)
    print(f"  Next state: {next_state}")
    
    print("\n✅ Decision engine test complete")