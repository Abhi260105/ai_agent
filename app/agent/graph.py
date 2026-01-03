"""
LangGraph State Machine Implementation
Orchestrates the agent's execution flow with state management
"""
from typing import Dict, Any, Literal, Optional
from datetime import datetime
import time

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.schemas.state_schema import AgentState
from app.schemas.graph_schema import GraphState, NodeOutput, GraphExecutionResult
from app.schemas.execution_schema import RetryContext, ProgressReport
from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.evaluator import evaluator
from app.agent.decision_engine import decision_engine
from app.utils.logger import get_logger

logger = get_logger("agent.graph")


class AgentGraph:
    """
    LangGraph-based agent orchestration
    Manages state transitions and execution flow
    """
    
    def __init__(self):
        self.logger = logger
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the state graph
        
        Flow:
        START → plan → execute → evaluate → decide → [continue/retry/replan/escalate/complete]
        """
        # Create state graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("evaluate", self._evaluate_node)
        graph.add_node("decide", self._decide_node)
        graph.add_node("replan", self._replan_node)
        graph.add_node("escalate", self._escalate_node)
        
        # Set entry point
        graph.set_entry_point("plan")
        
        # Add edges
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", "evaluate")
        graph.add_edge("evaluate", "decide")
        
        # Add conditional edges from decide node
        graph.add_conditional_edges(
            "decide",
            self._route_from_decide,
            {
                "continue": "execute",
                "retry": "execute",
                "replan": "replan",
                "escalate": "escalate",
                "complete": END,
                "abort": END
            }
        )
        
        graph.add_edge("replan", "execute")
        graph.add_edge("escalate", "decide")
        
        return graph.compile(checkpointer=self.checkpointer)
    
    # =========================================================================
    # NODE IMPLEMENTATIONS
    # =========================================================================
    
    def _plan_node(self, state: AgentState) -> AgentState:
        """
        Planning node - creates execution plan from goal
        """
        self.logger.info("PLAN NODE", goal=state.user_goal)
        
        start_time = time.time()
        state.update_status("planning")
        
        try:
            # Create plan
            plan = planner.create_plan(
                goal=state.user_goal,
                context=state.execution_context.metadata,
                use_memory=True
            )
            
            state.plan = plan
            state.add_action(f"Created plan with {len(plan.steps)} steps")
            
            self.logger.info(
                "Plan created",
                plan_id=plan.id,
                steps=len(plan.steps)
            )
            
        except Exception as e:
            self.logger.error("Planning failed", error=str(e))
            state.update_status("failed")
            state.final_result = {
                "error": f"Planning failed: {str(e)}"
            }
            state.should_continue = False
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"Plan node completed in {duration:.2f}ms")
        
        return state
    
    def _execute_node(self, state: AgentState) -> AgentState:
        """
        Execution node - executes next available step
        """
        self.logger.info("EXECUTE NODE")
        
        start_time = time.time()
        state.update_status("executing")
        
        try:
            # Get next step to execute
            next_step = state.get_next_executable_step()
            
            if not next_step:
                self.logger.info("No executable steps remaining")
                state.update_status("completed")
                return state
            
            self.logger.info(
                "Executing step",
                step_id=next_step.id,
                action=next_step.action
            )
            
            state.current_step = next_step
            
            # Check if this is a retry
            retry_context = None
            if next_step.id in state.execution_context.retry_count:
                retry_context = RetryContext(
                    step_id=next_step.id,
                    total_attempts=state.execution_context.retry_count[next_step.id],
                    max_attempts=next_step.max_retries
                )
            
            # Execute step
            result = executor.execute_step(next_step, state, retry_context)
            
            # Store result in state metadata
            state.execution_context.metadata[f"{next_step.id}_result"] = result.model_dump()
            
        except Exception as e:
            self.logger.error("Execution failed", error=str(e), exc_info=True)
            if state.current_step:
                state.execution_context.mark_step_failed(
                    state.current_step.id,
                    str(e)
                )
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"Execute node completed in {duration:.2f}ms")
        
        return state
    
    def _evaluate_node(self, state: AgentState) -> AgentState:
        """
        Evaluation node - evaluates step execution result
        """
        self.logger.info("EVALUATE NODE")
        
        start_time = time.time()
        state.update_status("evaluating")
        
        try:
            if not state.current_step:
                self.logger.warning("No current step to evaluate")
                return state
            
            # Get step result from metadata
            result_key = f"{state.current_step.id}_result"
            result_dict = state.execution_context.metadata.get(result_key)
            
            if not result_dict:
                self.logger.error("Step result not found")
                state.execution_context.mark_step_failed(
                    state.current_step.id,
                    "Result not found"
                )
                return state
            
            # Reconstruct ToolResult from dict
            from app.schemas.tool_schema import ToolResult
            result = ToolResult(**result_dict)
            
            # Evaluate
            success, confidence, error_ctx = evaluator.evaluate_step(
                state.current_step,
                result,
                state
            )
            
            if success:
                # Mark step as completed
                state.execution_context.mark_step_completed(
                    state.current_step.id,
                    result.data
                )
                
                self.logger.info(
                    "Step evaluated as successful",
                    step_id=state.current_step.id,
                    confidence=confidence
                )
                
                state.add_action(
                    f"✓ {state.current_step.action} completed (confidence: {confidence:.0%})"
                )
            else:
                # Mark step as failed
                state.execution_context.mark_step_failed(
                    state.current_step.id,
                    error_ctx.error_message if error_ctx else "Unknown error"
                )
                
                self.logger.warning(
                    "Step evaluated as failed",
                    step_id=state.current_step.id,
                    error_type=error_ctx.error_type if error_ctx else "unknown"
                )
                
                # Store error context
                state.execution_context.metadata["last_error"] = (
                    error_ctx.model_dump() if error_ctx else {}
                )
            
        except Exception as e:
            self.logger.error("Evaluation failed", error=str(e), exc_info=True)
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"Evaluate node completed in {duration:.2f}ms")
        
        return state
    
    def _decide_node(self, state: AgentState) -> AgentState:
        """
        Decision node - determines next action
        """
        self.logger.info("DECIDE NODE")
        
        start_time = time.time()
        
        try:
            # Get error context if last step failed
            error_dict = state.execution_context.metadata.get("last_error")
            error_ctx = None
            if error_dict:
                from app.schemas.execution_schema import ErrorContext
                error_ctx = ErrorContext(**error_dict)
            
            # Get retry context if applicable
            retry_ctx = None
            if state.current_step:
                retry_count = state.execution_context.retry_count.get(
                    state.current_step.id, 0
                )
                if retry_count > 0:
                    retry_ctx = RetryContext(
                        step_id=state.current_step.id,
                        total_attempts=retry_count,
                        max_attempts=state.current_step.max_retries
                    )
            
            # Make routing decision
            next_action = decision_engine.route_next_state(
                state=state,
                error=error_ctx,
                retry_context=retry_ctx
            )
            
            self.logger.info("Routing decision", next_action=next_action)
            
            # Store decision in metadata
            state.execution_context.metadata["next_action"] = next_action
            
            # Update state based on decision
            if next_action == "complete":
                state.update_status("completed")
                state.should_continue = False
                state.add_action("✓ All steps completed successfully")
                
            elif next_action == "abort":
                state.update_status("aborted")
                state.should_continue = False
                state.add_action("✗ Execution aborted")
                
            elif next_action == "retry" and state.current_step:
                # Increment retry count
                state.execution_context.increment_retry(state.current_step.id)
                state.add_action(f"↻ Retrying {state.current_step.action}")
                
        except Exception as e:
            self.logger.error("Decision failed", error=str(e), exc_info=True)
            state.execution_context.metadata["next_action"] = "abort"
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"Decide node completed in {duration:.2f}ms")
        
        return state
    
    def _replan_node(self, state: AgentState) -> AgentState:
        """
        Replanning node - creates new plan
        """
        self.logger.info("REPLAN NODE")
        
        start_time = time.time()
        state.update_status("replanning")
        
        try:
            reason = "Step failures require new approach"
            
            # Create new plan
            new_plan = planner.replan(state, reason)
            
            state.plan = new_plan
            state.add_action(f"↻ Created new plan with {len(new_plan.steps)} steps")
            
            # Reset execution context for remaining steps
            # Keep completed steps
            
            self.logger.info(
                "Replanning complete",
                new_plan_id=new_plan.id,
                steps=len(new_plan.steps)
            )
            
        except Exception as e:
            self.logger.error("Replanning failed", error=str(e))
            state.update_status("failed")
            state.should_continue = False
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"Replan node completed in {duration:.2f}ms")
        
        return state
    
    def _escalate_node(self, state: AgentState) -> AgentState:
        """
        Escalation node - requests user input
        """
        self.logger.info("ESCALATE NODE")
        
        state.needs_user_input = True
        state.user_prompt = "Human intervention required. Please review the situation."
        
        error_dict = state.execution_context.metadata.get("last_error")
        if error_dict:
            from app.schemas.execution_schema import ErrorContext
            error_ctx = ErrorContext(**error_dict)
            state.user_prompt += f"\n\nError: {error_ctx.error_message}"
            if error_ctx.suggested_actions:
                state.user_prompt += f"\n\nSuggested actions:\n"
                for action in error_ctx.suggested_actions:
                    state.user_prompt += f"- {action}\n"
        
        self.logger.info("Escalation complete, awaiting user input")
        
        return state
    
    # =========================================================================
    # ROUTING LOGIC
    # =========================================================================
    
    def _route_from_decide(self, state: AgentState) -> str:
        """
        Route from decide node based on decision
        """
        next_action = state.execution_context.metadata.get("next_action", "abort")
        self.logger.debug("Routing from decide", next_action=next_action)
        return next_action
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    def run(
        self,
        goal: str,
        thread_id: Optional[str] = None
    ) -> GraphExecutionResult:
        """
        Run the agent graph
        
        Args:
            goal: User's goal
            thread_id: Optional thread ID for checkpointing
            
        Returns:
            GraphExecutionResult
        """
        self.logger.info("Starting graph execution", goal=goal)
        
        start_time = time.time()
        
        # Create initial state
        initial_state = AgentState(
            user_goal=goal,
            user_input_raw=goal,
            status="initializing"
        )
        
        # Configure graph execution
        config = {"configurable": {"thread_id": thread_id or "default"}}
        
        try:
            # Run graph
            final_state = None
            for state in self.graph.stream(initial_state, config):
                # State is a dict with node name as key
                for node_name, node_state in state.items():
                    self.logger.debug(f"Node '{node_name}' executed")
                    final_state = node_state
            
            if not final_state:
                raise RuntimeError("Graph execution produced no final state")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Create result
            result = GraphExecutionResult(
                final_state=final_state,
                status="success" if final_state.status == "completed" else "failed",
                nodes_executed=[],  # TODO: Track nodes
                total_cycles=0,
                execution_time_seconds=duration
            )
            
            self.logger.info(
                "Graph execution complete",
                status=result.status,
                duration=duration
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Graph execution failed", error=str(e), exc_info=True)
            
            duration = time.time() - start_time
            
            return GraphExecutionResult(
                final_state=initial_state,
                status="failed",
                nodes_executed=[],
                total_cycles=0,
                execution_time_seconds=duration,
                error_message=str(e)
            )


# Global graph instance
agent_graph = AgentGraph()


if __name__ == "__main__":
    """Test agent graph"""
    
    print("🔄 Testing Agent Graph...")
    
    try:
        result = agent_graph.run(
            goal="Check my emails and schedule meetings"
        )
        
        print(f"\n✅ Graph execution complete")
        print(f"   Status: {result.status}")
        print(f"   Duration: {result.execution_time_seconds:.2f}s")
        print(f"   Final state: {result.final_state.status}")
        
        if result.final_state.action_summary:
            print(f"\n📝 Actions taken:")
            for action in result.final_state.action_summary:
                print(f"   {action}")
        
    except Exception as e:
        print(f"\n❌ Graph test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Graph test complete")