"""
Executor - Executes plans using tools
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class Executor:
    """Executes plans using available tools."""
    
    def __init__(self, tool_manager=None, memory=None):
        """
        Initialize executor.
        
        Args:
            tool_manager: Tool manager instance
            memory: Memory system instance
        """
        self.tool_manager = tool_manager
        self.memory = memory
        self.execution_context = {}
        self.metrics = {
            'total_steps': 0,
            'successful_steps': 0,
            'failed_steps': 0,
            'total_duration': 0
        }
        self.resources_cleaned = False
    
    async def execute_plan(
        self,
        plan: List[Dict],
        context: Optional[Dict] = None,
        parallel: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a plan.
        
        Args:
            plan: List of plan steps
            context: Execution context
            parallel: Execute independent steps in parallel
            progress_callback: Callback for progress updates
            
        Returns:
            Execution results
        """
        logger.info(f"Executing plan with {len(plan)} steps")
        
        start_time = datetime.now()
        self.execution_context = context or {}
        
        results = []
        tools_used = []
        
        try:
            for i, step in enumerate(plan):
                if progress_callback:
                    progress = int(((i + 1) / len(plan)) * 40 + 40)  # 40-80% range
                    progress_callback({
                        'step': f"Step {i+1}/{len(plan)}",
                        'progress': progress
                    })
                
                result = await self.execute_step(
                    step,
                    context=self.execution_context
                )
                
                results.append(result)
                
                # Track tool usage
                if result.get('tool'):
                    tools_used.append(result['tool'])
                
                # Update context with result
                self.execution_context[f'step_{step["step"]}_result'] = result
                
                # Stop if step failed critically
                if result.get('status') == 'error' and result.get('critical', False):
                    break
            
            # Determine overall status
            failed_count = sum(1 for r in results if r.get('status') == 'error')
            
            if failed_count == 0:
                status = 'success'
            elif failed_count < len(results):
                status = 'partial'
            else:
                status = 'failed'
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': status,
                'steps': results,
                'tools_used': list(set(tools_used)),
                'duration': duration,
                'result': self._extract_final_result(results)
            }
            
        except Exception as e:
            logger.error(f"Plan execution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'steps': results,
                'tools_used': list(set(tools_used)),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def execute_step(
        self,
        step: Dict,
        context: Optional[Dict] = None,
        max_retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a single step.
        
        Args:
            step: Step to execute
            context: Execution context
            max_retries: Maximum retry attempts
            timeout: Step timeout in seconds
            
        Returns:
            Step execution result
        """
        self.metrics['total_steps'] += 1
        
        step_num = step.get('step', 0)
        action = step.get('action', '')
        tool_name = step.get('tool')
        
        logger.info(f"Executing step {step_num}: {action}")
        
        for attempt in range(max_retries):
            try:
                # Get tool
                if tool_name and self.tool_manager:
                    tool = self.tool_manager.get_tool(tool_name)
                    
                    # Execute tool with timeout
                    result = await asyncio.wait_for(
                        tool.execute(step.get('params', {})),
                        timeout=timeout
                    )
                    
                    if result.get('status') == 'success':
                        self.metrics['successful_steps'] += 1
                        return {
                            'step': step_num,
                            'status': 'success',
                            'action': action,
                            'tool': tool_name,
                            'result': result.get('result'),
                            'attempt': attempt + 1
                        }
                    
                    # If failed and have retries left, continue
                    if attempt < max_retries - 1:
                        logger.warning(f"Step {step_num} failed, retrying...")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
                    # All retries exhausted
                    self.metrics['failed_steps'] += 1
                    return {
                        'step': step_num,
                        'status': 'error',
                        'action': action,
                        'tool': tool_name,
                        'error': result.get('error', 'Tool execution failed'),
                        'attempt': attempt + 1
                    }
                else:
                    # No tool specified, just mark as done
                    self.metrics['successful_steps'] += 1
                    return {
                        'step': step_num,
                        'status': 'success',
                        'action': action,
                        'result': f"Completed: {action}"
                    }
                    
            except asyncio.TimeoutError:
                logger.warning(f"Step {step_num} timed out (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    continue
                
                self.metrics['failed_steps'] += 1
                return {
                    'step': step_num,
                    'status': 'timeout',
                    'action': action,
                    'error': f'Timeout after {timeout}s'
                }
                
            except Exception as e:
                logger.error(f"Step {step_num} error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                self.metrics['failed_steps'] += 1
                return {
                    'step': step_num,
                    'status': 'error',
                    'action': action,
                    'error': str(e)
                }
        
        # Should not reach here
        return {
            'step': step_num,
            'status': 'error',
            'error': 'Max retries exceeded'
        }
    
    def _extract_final_result(self, results: List[Dict]) -> str:
        """Extract final result from step results."""
        if not results:
            return "No results"
        
        # Get result from last successful step
        for result in reversed(results):
            if result.get('status') == 'success' and result.get('result'):
                return result['result']
        
        return "Task completed"
    
    def get_tool(self, tool_name: str):
        """Get a tool by name."""
        if self.tool_manager:
            return self.tool_manager.get_tool(tool_name)
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        metrics = self.metrics.copy()
        
        if metrics['total_steps'] > 0:
            metrics['success_rate'] = (
                metrics['successful_steps'] / metrics['total_steps']
            ) * 100
            
            if metrics['total_duration'] > 0:
                metrics['average_duration'] = (
                    metrics['total_duration'] / metrics['total_steps']
                )
        
        return metrics
    
    def cancel(self):
        """Cancel current execution."""
        logger.info("Execution cancelled by user")
        # Implementation would set a flag to stop execution
        pass