"""
Core Agent - Main agent orchestrator

Integrates planner, executor, evaluator, memory, and tools.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Agent:
    """
    Main AI Agent that orchestrates task execution.
    
    Integrates:
    - Planner: Creates execution plans
    - Executor: Executes plans using tools
    - Evaluator: Evaluates results
    - Memory: Stores and retrieves context
    - LLM: Language model interface
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        use_memory: bool = True,
        max_iterations: int = 10,
        **kwargs
    ):
        """
        Initialize the agent.
        
        Args:
            llm_provider: LLM provider to use (openai, anthropic, local)
            use_memory: Whether to use memory system
            max_iterations: Maximum iterations for task execution
            **kwargs: Additional configuration
        """
        self.llm_provider = llm_provider
        self.use_memory = use_memory
        self.max_iterations = max_iterations
        self.config = kwargs
        
        # Components (initialized in initialize())
        self.planner = None
        self.executor = None
        self.evaluator = None
        self.memory = None
        self.llm = None
        self.tool_manager = None
        self.storage = None
        
        # State
        self.task_history = []
        self.is_initialized = False
        
        logger.info(f"Agent created with provider: {llm_provider}")
    
    async def initialize(self):
        """Initialize all agent components."""
        if self.is_initialized:
            logger.warning("Agent already initialized")
            return
        
        logger.info("Initializing agent components...")
        
        try:
            # Initialize LLM service
            from app.services.llm_service import LLMService
            self.llm = LLMService(provider=self.llm_provider)
            logger.info("✓ LLM service initialized")
            
            # Initialize storage
            from app.services.storage_service import StorageService
            self.storage = StorageService()
            logger.info("✓ Storage service initialized")
            
            # Initialize memory if enabled
            if self.use_memory:
                from app.core.memory import MemorySystem
                self.memory = MemorySystem(llm_service=self.llm, storage=self.storage)
                await self.memory.initialize()
                logger.info("✓ Memory system initialized")
            
            # Initialize tool manager
            from app.tools.base_tool import ToolManager
            self.tool_manager = ToolManager()
            await self.tool_manager.initialize()
            logger.info("✓ Tool manager initialized")
            
            # Initialize planner
            from app.core.planner import Planner
            self.planner = Planner(llm_service=self.llm, memory=self.memory)
            logger.info("✓ Planner initialized")
            
            # Initialize executor
            from app.core.executor import Executor
            self.executor = Executor(
                tool_manager=self.tool_manager,
                memory=self.memory
            )
            logger.info("✓ Executor initialized")
            
            # Initialize evaluator
            from app.core.evaluator import Evaluator
            self.evaluator = Evaluator(llm_service=self.llm)
            logger.info("✓ Evaluator initialized")
            
            self.is_initialized = True
            logger.info("Agent initialization complete!")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise
    
    async def execute_task(
        self,
        task: str,
        priority: str = "medium",
        timeout: int = 60,
        max_retries: int = 3,
        use_memory: Optional[bool] = None,
        allow_replanning: bool = True,
        progress_callback: Optional[Callable] = None,
        user_context: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a task from start to finish.
        
        Args:
            task: Task description
            priority: Task priority (low, medium, high, critical)
            timeout: Task timeout in seconds
            max_retries: Maximum retry attempts
            use_memory: Override default memory usage
            allow_replanning: Allow replanning on failure
            progress_callback: Callback for progress updates
            user_context: Additional user context
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with task results
        """
        if not self.is_initialized:
            await self.initialize()
        
        task_id = f"T-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Starting task {task_id}: {task}")
        
        start_time = datetime.now()
        
        # Override memory setting if specified
        _use_memory = use_memory if use_memory is not None else self.use_memory
        
        try:
            # Step 1: Gather context from memory
            context = {}
            if _use_memory and self.memory:
                if progress_callback:
                    progress_callback({'step': 'Loading context', 'progress': 10})
                
                context = await self._gather_context(task, user_context)
                logger.info(f"Gathered {len(context.get('memories', []))} relevant memories")
            
            # Step 2: Create execution plan
            if progress_callback:
                progress_callback({'step': 'Creating plan', 'progress': 20})
            
            plan = await self.planner.create_plan(
                task,
                context=context,
                priority=priority,
                **kwargs
            )
            logger.info(f"Created plan with {len(plan)} steps")
            
            # Step 3: Execute plan
            if progress_callback:
                progress_callback({'step': 'Executing plan', 'progress': 40})
            
            execution_result = await self._execute_with_retry(
                plan=plan,
                max_retries=max_retries,
                timeout=timeout,
                allow_replanning=allow_replanning,
                progress_callback=progress_callback,
                context=context
            )
            
            # Step 4: Evaluate results
            if progress_callback:
                progress_callback({'step': 'Evaluating results', 'progress': 80})
            
            evaluation = await self.evaluator.evaluate_result(
                execution_result,
                goal=task
            )
            logger.info(f"Evaluation score: {evaluation.get('score', 0):.2f}")
            
            # Step 5: Store in memory
            if _use_memory and self.memory:
                if progress_callback:
                    progress_callback({'step': 'Storing results', 'progress': 90})
                
                await self._store_task_memory(task, execution_result, evaluation)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Build result
            result = {
                'task_id': task_id,
                'task': task,
                'status': execution_result.get('status', 'unknown'),
                'result': execution_result.get('result'),
                'plan': plan,
                'steps': execution_result.get('steps', []),
                'evaluation': evaluation,
                'duration': duration,
                'created_at': start_time.isoformat(),
                'completed_at': datetime.now().isoformat(),
                'used_memory': _use_memory,
                'tools_used': execution_result.get('tools_used', []),
                'metadata': {
                    'priority': priority,
                    'retries': execution_result.get('retries', 0),
                    'replanned': execution_result.get('replanned', False)
                }
            }
            
            # Store in history
            self.task_history.append(result)
            
            if progress_callback:
                progress_callback({'step': 'Complete', 'progress': 100})
            
            logger.info(f"Task {task_id} completed in {duration:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {timeout}s")
            return {
                'task_id': task_id,
                'task': task,
                'status': 'timeout',
                'error': f'Task timed out after {timeout} seconds',
                'duration': timeout
            }
        
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
            return {
                'task_id': task_id,
                'task': task,
                'status': 'failed',
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def _gather_context(
        self,
        task: str,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Gather relevant context from memory."""
        context = {}
        
        if self.memory:
            # Search for relevant memories
            relevant_memories = await self.memory.search(
                task,
                limit=5,
                similarity_threshold=0.7
            )
            
            context['memories'] = relevant_memories
            
            # Get user preferences
            preferences = await self.memory.filter(
                memory_type='semantic',
                tags=['preferences'],
                limit=10
            )
            context['preferences'] = preferences
        
        # Add user-provided context
        if user_context:
            context['user_context'] = user_context
        
        return context
    
    async def _execute_with_retry(
        self,
        plan: List[Dict],
        max_retries: int,
        timeout: int,
        allow_replanning: bool,
        progress_callback: Optional[Callable],
        context: Dict
    ) -> Dict[str, Any]:
        """Execute plan with retry and replanning logic."""
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                # Execute plan with timeout
                execution_result = await asyncio.wait_for(
                    self.executor.execute_plan(
                        plan,
                        context=context,
                        progress_callback=progress_callback
                    ),
                    timeout=timeout
                )
                
                # Check if successful
                if execution_result.get('status') == 'success':
                    execution_result['retries'] = retries
                    return execution_result
                
                # If failed and replanning allowed, try to replan
                if allow_replanning and retries < max_retries:
                    logger.warning(f"Execution failed, attempting replan (attempt {retries + 1})")
                    
                    # Create new plan based on what failed
                    plan = await self.planner.refine_plan(
                        plan,
                        feedback=execution_result.get('error', 'Execution failed')
                    )
                    
                    retries += 1
                    continue
                
                # No more retries
                execution_result['retries'] = retries
                return execution_result
                
            except asyncio.TimeoutError:
                logger.warning(f"Execution timeout (attempt {retries + 1})")
                last_error = "Execution timed out"
                retries += 1
                
            except Exception as e:
                logger.error(f"Execution error (attempt {retries + 1}): {str(e)}")
                last_error = str(e)
                retries += 1
        
        # All retries exhausted
        return {
            'status': 'failed',
            'error': last_error or 'Max retries exceeded',
            'retries': retries,
            'steps': []
        }
    
    async def _store_task_memory(
        self,
        task: str,
        execution_result: Dict,
        evaluation: Dict
    ):
        """Store task execution in memory."""
        if not self.memory:
            return
        
        try:
            # Store task completion
            await self.memory.store({
                'content': f"Completed task: {task}",
                'memory_type': 'episodic',
                'importance': 'medium',
                'tags': ['task_completion', 'execution'],
                'metadata': {
                    'task': task,
                    'status': execution_result.get('status'),
                    'score': evaluation.get('score'),
                    'duration': execution_result.get('duration')
                }
            })
            
            # Store learnings if successful
            if execution_result.get('status') == 'success':
                await self.memory.store({
                    'content': f"Successfully executed: {task}",
                    'memory_type': 'semantic',
                    'importance': 'high',
                    'tags': ['success', 'learning']
                })
            
        except Exception as e:
            logger.warning(f"Failed to store task memory: {str(e)}")
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Have a conversation with the agent.
        
        Args:
            message: User message
            conversation_history: Previous messages
            use_memory: Whether to use memory for context
            
        Returns:
            Agent response with metadata
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Build conversation context
        messages = conversation_history or []
        
        # Add memory context if enabled
        context = ""
        if use_memory and self.memory:
            relevant_memories = await self.memory.search(message, limit=3)
            if relevant_memories:
                context = "Relevant context:\n" + "\n".join([
                    m['content'] for m in relevant_memories
                ])
        
        # Add current message
        messages.append({
            'role': 'user',
            'content': message
        })
        
        # Generate response
        response = await self.llm.chat(
            messages,
            system_message=context if context else None
        )
        
        return {
            'message': response.get('content'),
            'tokens': response.get('tokens'),
            'context_used': bool(context)
        }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        if self.tool_manager:
            return self.tool_manager.list_tools()
        return []
    
    async def get_task_history(self, limit: int = 10) -> List[Dict]:
        """Get recent task history."""
        return self.task_history[-limit:] if self.task_history else []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        stats = {
            'total_tasks': len(self.task_history),
            'successful_tasks': sum(
                1 for t in self.task_history 
                if t.get('status') == 'success'
            ),
            'failed_tasks': sum(
                1 for t in self.task_history 
                if t.get('status') == 'failed'
            ),
            'average_duration': 0,
            'tools_available': len(self.get_available_tools()) if self.tool_manager else 0
        }
        
        if self.task_history:
            total_duration = sum(
                t.get('duration', 0) for t in self.task_history
            )
            stats['average_duration'] = total_duration / len(self.task_history)
        
        # Add memory stats
        if self.memory:
            memory_stats = await self.memory.get_statistics()
            stats['memory'] = memory_stats
        
        # Add LLM stats
        if self.llm:
            llm_stats = self.llm.get_statistics()
            stats['llm'] = llm_stats
        
        return stats
    
    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info("Cleaning up agent resources...")
        
        try:
            if self.tool_manager:
                await self.tool_manager.cleanup()
            
            if self.memory:
                await self.memory.cleanup()
            
            if self.llm:
                self.llm.clear_history()
            
            self.is_initialized = False
            logger.info("Agent cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def __repr__(self) -> str:
        """String representation of agent."""
        return (
            f"Agent(provider={self.llm_provider}, "
            f"memory={'enabled' if self.use_memory else 'disabled'}, "
            f"initialized={self.is_initialized})"
        )


# Convenience function
async def create_agent(
    llm_provider: str = "openai",
    **kwargs
) -> Agent:
    """
    Create and initialize an agent.
    
    Args:
        llm_provider: LLM provider to use
        **kwargs: Additional agent configuration
        
    Returns:
        Initialized Agent instance
    """
    agent = Agent(llm_provider=llm_provider, **kwargs)
    await agent.initialize()
    return agent