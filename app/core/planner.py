"""
Planner - Creates execution plans for tasks
"""

import logging
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class Planner:
    """Creates and refines execution plans for tasks."""
    
    def __init__(self, llm_service=None, memory=None):
        """
        Initialize planner.
        
        Args:
            llm_service: LLM service instance
            memory: Memory system instance
        """
        self.llm = llm_service
        self.memory = memory
    
    async def create_plan(
        self,
        task: str,
        context: Optional[Dict] = None,
        priority: str = "medium",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Create execution plan for a task.
        
        Args:
            task: Task description
            context: Additional context
            priority: Task priority
            **kwargs: Additional parameters
            
        Returns:
            List of plan steps
        """
        logger.info(f"Creating plan for: {task}")
        
        # Build prompt for LLM
        prompt = self._build_planning_prompt(task, context, priority)
        
        # Generate plan using LLM
        if self.llm:
            response = await self.llm.generate(
                prompt,
                temperature=0.3,  # Lower temperature for more focused planning
                max_tokens=1000
            )
            
            # Parse plan from response
            plan = self._parse_plan(response.get('content', ''))
        else:
            # Fallback: simple plan
            plan = self._create_simple_plan(task)
        
        # Validate plan
        if not self.validate_plan(plan):
            logger.warning("Generated plan failed validation, using simple plan")
            plan = self._create_simple_plan(task)
        
        return plan
    
    async def refine_plan(
        self,
        plan: List[Dict],
        feedback: str
    ) -> List[Dict[str, Any]]:
        """
        Refine plan based on feedback.
        
        Args:
            plan: Original plan
            feedback: Feedback or error message
            
        Returns:
            Refined plan
        """
        logger.info(f"Refining plan based on feedback: {feedback}")
        
        if self.llm:
            prompt = f"""
Original plan:
{json.dumps(plan, indent=2)}

Feedback: {feedback}

Please provide a refined plan that addresses the feedback.
Return the plan as a JSON array of steps.
"""
            
            response = await self.llm.generate(prompt, temperature=0.3)
            refined_plan = self._parse_plan(response.get('content', ''))
            
            if self.validate_plan(refined_plan):
                return refined_plan
        
        # Fallback: return original plan
        return plan
    
    def _build_planning_prompt(
        self,
        task: str,
        context: Optional[Dict],
        priority: str
    ) -> str:
        """Build prompt for plan generation."""
        prompt = f"""Create a step-by-step execution plan for this task:

Task: {task}
Priority: {priority}

"""
        
        if context and context.get('memories'):
            prompt += "Relevant context:\n"
            for mem in context['memories'][:3]:
                prompt += f"- {mem['content']}\n"
            prompt += "\n"
        
        prompt += """Please provide a detailed plan as a JSON array where each step has:
- step: step number (integer)
- action: what to do (string)
- tool: which tool to use (string, if applicable)
- description: detailed description (string)

Return ONLY the JSON array, no other text."""
        
        return prompt
    
    def _parse_plan(self, content: str) -> List[Dict[str, Any]]:
        """Parse plan from LLM response."""
        try:
            # Try to extract JSON from response
            content = content.strip()
            
            # Remove markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            # Parse JSON
            plan = json.loads(content)
            
            # Ensure it's a list
            if isinstance(plan, dict) and 'plan' in plan:
                plan = plan['plan']
            
            if not isinstance(plan, list):
                raise ValueError("Plan must be a list")
            
            return plan
            
        except Exception as e:
            logger.warning(f"Failed to parse plan: {str(e)}")
            return []
    
    def _create_simple_plan(self, task: str) -> List[Dict[str, Any]]:
        """Create a simple fallback plan."""
        return [
            {
                'step': 1,
                'action': 'execute_task',
                'description': task,
                'tool': 'generic_executor'
            }
        ]
    
    def validate_plan(self, plan: List[Dict]) -> bool:
        """
        Validate plan structure.
        
        Args:
            plan: Plan to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(plan, list) or len(plan) == 0:
            return False
        
        for step in plan:
            if not isinstance(step, dict):
                return False
            if 'step' not in step or 'action' not in step:
                return False
        
        return True
    
    def estimate_duration(self, plan: List[Dict]) -> float:
        """Estimate plan execution time in seconds."""
        total_time = 0
        
        for step in plan:
            # Default estimate: 5 seconds per step
            estimated_time = step.get('estimated_time', 5)
            total_time += estimated_time
        
        return total_time
    
    def identify_parallel_steps(self, plan: List[Dict]) -> List[List[int]]:
        """Identify steps that can run in parallel."""
        parallel_groups = []
        current_group = []
        
        for step in plan:
            depends_on = step.get('depends_on', [])
            
            if not depends_on:
                # No dependencies, can run in parallel with others
                current_group.append(step['step'])
            else:
                # Has dependencies, start new group
                if current_group:
                    parallel_groups.append(current_group)
                    current_group = []
                parallel_groups.append([step['step']])
        
        if current_group:
            parallel_groups.append(current_group)
        
        return parallel_groups
    
    def serialize_plan(self, plan: List[Dict]) -> str:
        """Serialize plan to JSON string."""
        return json.dumps(plan, indent=2)
    
    def deserialize_plan(self, plan_str: str) -> List[Dict]:
        """Deserialize plan from JSON string."""
        return json.loads(plan_str)