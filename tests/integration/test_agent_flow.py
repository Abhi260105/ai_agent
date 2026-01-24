"""
Integration tests for complete agent workflows.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio


class TestAgentFlowIntegration:
    """Test complete agent execution flows."""
    
    @pytest.fixture
    async def agent(self):
        """Create a complete agent instance."""
        from app.core.agent import Agent
        agent = Agent()
        await agent.initialize()
        yield agent
        await agent.cleanup()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_simple_task_flow(self, agent):
        """Test simple task from start to finish."""
        task = "Search for recent AI news and summarize the top 3 articles"
        
        result = await agent.execute_task(task)
        
        assert result is not None
        assert result['status'] in ['success', 'completed']
        assert 'result' in result
        assert len(result.get('steps', [])) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_step_workflow(self, agent):
        """Test complex multi-step workflow."""
        task = """
        1. Read the sales data file
        2. Calculate the total revenue
        3. Create a summary report
        4. Save the report to a file
        """
        
        result = await agent.execute_task(task)
        
        assert result['status'] == 'success'
        assert len(result['steps']) == 4
        assert all(step['status'] == 'success' for step in result['steps'])
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_with_memory_context(self, agent):
        """Test task execution using memory context."""
        # First, store some context
        await agent.memory.store({
            "content": "User prefers concise summaries",
            "memory_type": "semantic"
        })
        
        task = "Summarize the latest tech news"
        result = await agent.execute_task(task, use_memory=True)
        
        assert result['status'] == 'success'
        assert result.get('used_memory', False) is True
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_recovery_flow(self, agent):
        """Test that agent can recover from errors."""
        # Simulate a task that might fail initially
        task = "Connect to unavailable_service and fetch data"
        
        result = await agent.execute_task(task, max_retries=3)
        
        # Should either succeed after retry or fail gracefully
        assert result['status'] in ['success', 'failed']
        if result['status'] == 'failed':
            assert 'error' in result
            assert 'recovery_attempted' in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_tasks(self, agent):
        """Test executing multiple tasks concurrently."""
        tasks = [
            "Search for Python tutorials",
            "Check the weather forecast",
            "Calculate 15% of 200"
        ]
        
        results = await asyncio.gather(*[
            agent.execute_task(task) for task in tasks
        ])
        
        assert len(results) == 3
        assert all(r['status'] in ['success', 'completed'] for r in results)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_plan_execution_evaluation_cycle(self, agent):
        """Test the complete plan-execute-evaluate cycle."""
        task = "Find and summarize 3 articles about climate change"
        
        # Plan phase
        plan = await agent.planner.create_plan(task)
        assert len(plan) > 0
        
        # Execute phase
        execution_result = await agent.executor.execute_plan(plan)
        assert len(execution_result) == len(plan)
        
        # Evaluate phase
        evaluation = await agent.evaluator.evaluate_result(execution_result, goal=task)
        assert 'score' in evaluation
        assert evaluation['score'] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_adaptive_replanning(self, agent):
        """Test that agent can adapt and replan when needed."""
        task = "Complete task that requires adaptation"
        
        # Mock a situation where replanning is needed
        with patch.object(agent.executor, 'execute_plan') as mock_exec:
            # First execution fails
            mock_exec.side_effect = [
                {"status": "failed", "error": "Tool unavailable"},
                {"status": "success", "result": "Completed with alternative"}
            ]
            
            result = await agent.execute_task(task, allow_replanning=True)
            
            assert mock_exec.call_count == 2  # Original + replan
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tool_chain_execution(self, agent):
        """Test chaining multiple tools together."""
        task = "Search for a recipe, extract ingredients, and create shopping list"
        
        result = await agent.execute_task(task)
        
        assert result['status'] == 'success'
        # Verify multiple tools were used
        tools_used = result.get('tools_used', [])
        assert len(tools_used) >= 2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_long_running_task(self, agent):
        """Test handling of long-running tasks."""
        task = "Process large dataset with multiple analysis steps"
        
        # Use a callback to track progress
        progress_updates = []
        
        def progress_callback(update):
            progress_updates.append(update)
        
        result = await agent.execute_task(
            task,
            progress_callback=progress_callback,
            timeout=60
        )
        
        assert result['status'] in ['success', 'timeout']
        assert len(progress_updates) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_context_preservation(self, agent):
        """Test that context is preserved across steps."""
        task = "Calculate 10 + 5, then multiply the result by 2"
        
        result = await agent.execute_task(task)
        
        assert result['status'] == 'success'
        # Verify final result is 30
        assert '30' in str(result.get('result', ''))
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_interaction_flow(self, agent):
        """Test handling user interactions during execution."""
        task = "Create a personalized greeting"
        
        # Simulate user providing input
        user_inputs = {"name": "Alice", "preference": "formal"}
        
        result = await agent.execute_task(task, user_context=user_inputs)
        
        assert result['status'] == 'success'
        assert 'Alice' in result.get('result', '')
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_learning_loop(self, agent):
        """Test that agent learns from past executions."""
        # Execute similar task multiple times
        task = "Summarize tech news"
        
        result1 = await agent.execute_task(task)
        await agent.memory.store({
            "content": f"Task completed in {result1.get('duration', 0)}s",
            "memory_type": "episodic",
            "tags": ["performance", "tech_news"]
        })
        
        result2 = await agent.execute_task(task, use_memory=True)
        
        # Second execution should potentially be faster or better
        assert result2['status'] == 'success'
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_graceful_degradation(self, agent):
        """Test graceful degradation when tools are unavailable."""
        task = "Complete task even if some tools fail"
        
        # Simulate some tools being unavailable
        with patch.object(agent, 'get_available_tools') as mock_tools:
            mock_tools.return_value = ['basic_tool']  # Limited tools
            
            result = await agent.execute_task(task)
            
            assert result is not None
            # Should complete with available tools or report limitation
            assert result['status'] in ['success', 'partial', 'failed']
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_stress_test_rapid_tasks(self, agent):
        """Stress test with rapid task submissions."""
        tasks = [f"Task {i}" for i in range(20)]
        
        results = await asyncio.gather(*[
            agent.execute_task(task) for task in tasks
        ], return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
        assert successful >= len(tasks) * 0.8  # At least 80% success rate