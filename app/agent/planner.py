"""
Planner - Goal Decomposition Engine
Converts natural language goals into structured execution plans
Uses LLM with strict JSON schema enforcement
"""
from typing import List, Dict, Any, Optional
import json

from app.schemas.plan_schema import PlanSchema, StepSchema, PlanValidationResult
from app.schemas.state_schema import AgentState
from app.schemas.memory_schema import MemoryQuery
from app.services.llm_service import llm_service
from app.utils.logger import get_logger
from app.utils.validators import PlanValidator
from app.config import config

logger = get_logger("agent.planner")


class Planner:
    """
    Converts user goals into structured execution plans
    Features:
    - LLM-powered decomposition with JSON schema
    - Dependency analysis
    - Memory-informed planning (learns from past)
    - Plan validation and optimization
    - Risk assessment
    """
    
    def __init__(self):
        self.llm = llm_service
        self.logger = logger
        self.available_tools = self._get_available_tools()
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        # TODO: This will be populated from tool registry in Phase 3
        return [
            "email_tool",
            "calendar_tool",
            "web_search_tool",
            "file_tool"
        ]
    
    def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        use_memory: bool = True
    ) -> PlanSchema:
        """
        Create execution plan from goal
        
        Args:
            goal: User's objective
            context: Additional context
            use_memory: Whether to use past memories
            
        Returns:
            Validated PlanSchema
        """
        self.logger.info("Creating plan", goal=goal, use_memory=use_memory)
        
        try:
            # Retrieve relevant memories if enabled
            relevant_memories = []
            if use_memory:
                relevant_memories = self._retrieve_relevant_memories(goal)
                self.logger.debug(
                    "Retrieved memories",
                    count=len(relevant_memories)
                )
            
            # Generate plan using LLM
            plan = self._generate_plan_with_llm(
                goal=goal,
                context=context or {},
                memories=relevant_memories
            )
            
            # Validate plan
            validation = PlanValidator.validate_plan(plan)
            
            if not validation.is_valid:
                self.logger.warning(
                    "Plan validation failed",
                    errors=validation.errors
                )
                # Try to fix common issues
                plan = self._fix_plan_issues(plan, validation)
                
                # Re-validate
                validation = PlanValidator.validate_plan(plan)
                if not validation.is_valid:
                    raise ValueError(f"Cannot create valid plan: {validation.errors}")
            
            if validation.warnings:
                self.logger.warning("Plan warnings", warnings=validation.warnings)
            
            # Optimize plan
            plan = self._optimize_plan(plan)
            
            # Assess risks
            self._assess_plan_risks(plan)
            
            self.logger.info(
                "Plan created successfully",
                plan_id=plan.id,
                steps=len(plan.steps)
            )
            
            return plan
            
        except Exception as e:
            self.logger.error("Plan creation failed", error=str(e))
            raise
    
    def _generate_plan_with_llm(
        self,
        goal: str,
        context: Dict[str, Any],
        memories: List[Dict[str, Any]]
    ) -> PlanSchema:
        """
        Use LLM to generate plan
        Forces structured JSON output
        """
        # Build system prompt
        system_prompt = self._build_planning_prompt(memories)
        
        # Build user prompt
        user_prompt = f"""
Goal: {goal}

Available Tools:
{json.dumps(self.available_tools, indent=2)}

Context:
{json.dumps(context, indent=2) if context else "None"}

Create a detailed execution plan to achieve this goal.
Break it down into specific, actionable steps.
Each step must use one of the available tools.
Consider dependencies between steps.
"""
        
        self.logger.debug("Calling LLM for plan generation")
        
        try:
            # Use structured output to enforce schema
            plan = self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=PlanSchema,
                temperature=config.agent.temperature
            )
            
            return plan
            
        except Exception as e:
            self.logger.error("LLM plan generation failed", error=str(e))
            
            # Fallback: create simple plan
            self.logger.warning("Using fallback simple plan")
            return self._create_fallback_plan(goal)
    
    def _build_planning_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Build system prompt for planning"""
        
        base_prompt = """You are an expert task planner. Your job is to break down user goals into concrete, executable steps.

CRITICAL RULES:
1. Each step MUST use exactly ONE tool from the available tools
2. Steps must be atomic and specific
3. Consider dependencies - steps that need outputs from previous steps
4. Be realistic about what each tool can do
5. Think about error cases and provide fallback actions
6. Steps should be ordered logically

Step Properties:
- id: Unique identifier (step_1, step_2, etc.)
- action: Specific action to perform
- tool: Tool to use (must be from available tools)
- params: Parameters for the tool
- depends_on: IDs of steps that must complete first
- success_criteria: How to know if step succeeded
- failure_action: What to do if step fails (retry/skip/abort/replan)
- max_retries: How many times to retry (1-5)
- timeout_seconds: Maximum time for step (10-300)

Plan Properties:
- objective: Clear statement of what you're trying to achieve
- steps: List of steps (minimum 1, maximum 10)
- priority: low/medium/high/critical
- tags: List of relevant tags"""
        
        # Add memory context if available
        if memories:
            memory_context = "\n\nRELEVANT PAST EXPERIENCE:\n"
            for memory in memories[:3]:  # Limit to top 3
                memory_context += f"- {json.dumps(memory, indent=2)}\n"
            base_prompt += memory_context
        
        return base_prompt
    
    def _retrieve_relevant_memories(self, goal: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for planning
        TODO: Implement with memory system in Phase 1B
        """
        # Placeholder: Return empty list
        # In Phase 1B, this will query the memory system
        return []
    
    def _fix_plan_issues(
        self,
        plan: PlanSchema,
        validation: PlanValidationResult
    ) -> PlanSchema:
        """
        Attempt to fix common plan issues
        """
        self.logger.info("Attempting to fix plan issues")
        
        # Fix: Missing step IDs
        for i, step in enumerate(plan.steps):
            if not step.id or not step.id.startswith("step_"):
                step.id = f"step_{i+1}"
        
        # Fix: Invalid dependencies
        valid_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            step.depends_on = [
                dep for dep in step.depends_on
                if dep in valid_ids
            ]
        
        # Fix: Invalid tools
        for step in plan.steps:
            if step.tool not in self.available_tools:
                self.logger.warning(
                    f"Invalid tool '{step.tool}', defaulting to email_tool"
                )
                step.tool = "email_tool"
        
        return plan
    
    def _optimize_plan(self, plan: PlanSchema) -> PlanSchema:
        """
        Optimize plan for better execution
        - Remove redundant steps
        - Parallelize independent steps
        - Reorder for efficiency
        """
        self.logger.debug("Optimizing plan")
        
        # TODO: Implement optimization strategies
        # - Identify steps that can run in parallel
        # - Remove duplicate steps
        # - Reorder to minimize wait time
        
        return plan
    
    def _assess_plan_risks(self, plan: PlanSchema):
        """
        Assess risks in the plan
        Adds warnings to metadata
        """
        risks = []
        
        # Check for long chains of dependencies
        max_chain_length = self._max_dependency_chain(plan)
        if max_chain_length > 5:
            risks.append(f"Long dependency chain ({max_chain_length} steps)")
        
        # Check for steps with high timeout
        high_timeout_steps = [
            step for step in plan.steps
            if step.timeout_seconds > 120
        ]
        if high_timeout_steps:
            risks.append(f"{len(high_timeout_steps)} steps with long timeouts")
        
        # Check for external dependencies
        external_tools = ["web_search_tool", "email_tool", "calendar_tool"]
        external_steps = [
            step for step in plan.steps
            if step.tool in external_tools
        ]
        if external_steps:
            risks.append(f"{len(external_steps)} steps depend on external services")
        
        if risks:
            plan.context["risks"] = risks
            self.logger.warning("Plan risks identified", risks=risks)
    
    def _max_dependency_chain(self, plan: PlanSchema) -> int:
        """Calculate longest dependency chain in plan"""
        def chain_length(step_id: str, visited: set) -> int:
            if step_id in visited:
                return 0
            
            step = plan.get_step(step_id)
            if not step or not step.depends_on:
                return 1
            
            visited.add(step_id)
            max_dep_length = max(
                (chain_length(dep, visited.copy()) for dep in step.depends_on),
                default=0
            )
            return 1 + max_dep_length
        
        return max(
            (chain_length(step.id, set()) for step in plan.steps),
            default=0
        )
    
    def _create_fallback_plan(self, goal: str) -> PlanSchema:
        """
        Create simple fallback plan when LLM fails
        """
        self.logger.warning("Creating fallback plan")
        
        return PlanSchema(
            objective=goal,
            steps=[
                StepSchema(
                    id="step_1",
                    action="execute_goal",
                    tool="email_tool",  # Default tool
                    params={"goal": goal},
                    success_criteria="Task completed",
                    failure_action="abort"
                )
            ],
            priority="medium",
            tags=["fallback"]
        )
    
    def replan(
        self,
        state: AgentState,
        reason: str
    ) -> PlanSchema:
        """
        Create new plan based on current state
        
        Args:
            state: Current agent state
            reason: Why replanning is needed
            
        Returns:
            New plan
        """
        self.logger.info("Replanning", reason=reason)
        
        # Build context from current state
        context = {
            "reason_for_replan": reason,
            "completed_steps": state.execution_context.completed_steps,
            "failed_steps": state.execution_context.failed_steps,
            "errors": state.execution_context.errors[:3]  # Last 3 errors
        }
        
        # Create new plan
        new_plan = self.create_plan(
            goal=state.user_goal,
            context=context,
            use_memory=True
        )
        
        self.logger.info(
            "Replanning complete",
            new_plan_id=new_plan.id,
            steps=len(new_plan.steps)
        )
        
        return new_plan


# Global planner instance
planner = Planner()


if __name__ == "__main__":
    """Test planner"""
    
    print("🧠 Testing Planner...")
    
    # Test plan creation
    try:
        plan = planner.create_plan(
            goal="Check my emails and schedule any pending meetings",
            use_memory=False
        )
        
        print(f"\n✅ Plan created successfully!")
        print(f"   ID: {plan.id}")
        print(f"   Objective: {plan.objective}")
        print(f"   Steps: {len(plan.steps)}")
        
        for step in plan.steps:
            print(f"\n   Step {step.id}:")
            print(f"     Action: {step.action}")
            print(f"     Tool: {step.tool}")
            print(f"     Dependencies: {step.depends_on or 'None'}")
        
    except Exception as e:
        print(f"\n❌ Planner test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Planner test complete")