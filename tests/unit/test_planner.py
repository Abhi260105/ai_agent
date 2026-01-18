"""
Unit tests for Planner component.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestPlanner:
    """Test suite for the Planner component."""
    
    @pytest.fixture
    def planner(self):
        """Create a Planner instance for testing."""
        from app.core.planner import Planner
        return Planner()
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM service."""
        mock = AsyncMock()
        mock.generate.return_value = {
            "plan": [
                {"step": 1, "action": "search", "description": "Search for information"},
                {"step": 2, "action": "analyze", "description": "Analyze results"}
            ],
            "reasoning": "Breaking down the task into steps"
        }
        return mock
    
    def test_planner_initialization(self, planner):
        """Test that planner initializes correctly."""
        assert planner is not None
        assert hasattr(planner, 'create_plan')
        assert hasattr(planner, 'refine_plan')
    
    @pytest.mark.asyncio
    async def test_create_simple_plan(self, planner, mock_llm):
        """Test creating a simple execution plan."""
        with patch.object(planner, 'llm', mock_llm):
            task = "Find recent news about AI"
            plan = await planner.create_plan(task)
            
            assert plan is not None
            assert len(plan) > 0
            assert all('step' in item for item in plan)
            assert all('action' in item for item in plan)
    
    @pytest.mark.asyncio
    async def test_create_complex_plan(self, planner, mock_llm):
        """Test creating a complex multi-step plan."""
        complex_task = "Analyze sales data, create a report, and email it to the team"
        
        mock_llm.generate.return_value = {
            "plan": [
                {"step": 1, "action": "read_file", "description": "Read sales data"},
                {"step": 2, "action": "analyze", "description": "Analyze data"},
                {"step": 3, "action": "create_report", "description": "Create report"},
                {"step": 4, "action": "send_email", "description": "Email report"}
            ],
            "reasoning": "Multi-step workflow"
        }
        
        with patch.object(planner, 'llm', mock_llm):
            plan = await planner.create_plan(complex_task)
            
            assert len(plan) == 4
            assert plan[0]['action'] == 'read_file'
            assert plan[-1]['action'] == 'send_email'
    
    @pytest.mark.asyncio
    async def test_refine_plan_with_feedback(self, planner, mock_llm):
        """Test refining a plan based on feedback."""
        original_plan = [
            {"step": 1, "action": "search", "description": "Search"},
            {"step": 2, "action": "summarize", "description": "Summarize"}
        ]
        
        feedback = "Add a verification step before summarizing"
        
        mock_llm.generate.return_value = {
            "plan": [
                {"step": 1, "action": "search", "description": "Search"},
                {"step": 2, "action": "verify", "description": "Verify results"},
                {"step": 3, "action": "summarize", "description": "Summarize"}
            ],
            "reasoning": "Added verification step"
        }
        
        with patch.object(planner, 'llm', mock_llm):
            refined = await planner.refine_plan(original_plan, feedback)
            
            assert len(refined) == 3
            assert any(step['action'] == 'verify' for step in refined)
    
    def test_validate_plan_structure(self, planner):
        """Test plan validation."""
        valid_plan = [
            {"step": 1, "action": "search", "description": "Search"},
            {"step": 2, "action": "analyze", "description": "Analyze"}
        ]
        
        assert planner.validate_plan(valid_plan) is True
    
    def test_invalid_plan_structure(self, planner):
        """Test that invalid plans are rejected."""
        invalid_plan = [
            {"action": "search"},  # Missing step number
            {"step": 2, "description": "Analyze"}  # Missing action
        ]
        
        assert planner.validate_plan(invalid_plan) is False
    
    @pytest.mark.asyncio
    async def test_plan_with_dependencies(self, planner, mock_llm):
        """Test creating a plan with step dependencies."""
        task = "Book a meeting after checking calendar availability"
        
        mock_llm.generate.return_value = {
            "plan": [
                {"step": 1, "action": "check_calendar", "description": "Check availability"},
                {"step": 2, "action": "book_meeting", "description": "Book meeting", "depends_on": [1]}
            ],
            "reasoning": "Sequential dependency"
        }
        
        with patch.object(planner, 'llm', mock_llm):
            plan = await planner.create_plan(task)
            
            assert plan[1].get('depends_on') == [1]
    
    @pytest.mark.asyncio
    async def test_plan_error_handling(self, planner, mock_llm):
        """Test error handling in plan creation."""
        mock_llm.generate.side_effect = Exception("LLM service unavailable")
        
        with patch.object(planner, 'llm', mock_llm):
            with pytest.raises(Exception):
                await planner.create_plan("Test task")
    
    def test_estimate_plan_duration(self, planner):
        """Test estimating plan execution time."""
        plan = [
            {"step": 1, "action": "search", "estimated_time": 5},
            {"step": 2, "action": "analyze", "estimated_time": 10},
            {"step": 3, "action": "summarize", "estimated_time": 3}
        ]
        
        total_time = planner.estimate_duration(plan)
        assert total_time == 18
    
    @pytest.mark.asyncio
    async def test_parallel_steps_detection(self, planner):
        """Test detecting steps that can run in parallel."""
        plan = [
            {"step": 1, "action": "search_a", "description": "Search A"},
            {"step": 2, "action": "search_b", "description": "Search B"},
            {"step": 3, "action": "combine", "description": "Combine", "depends_on": [1, 2]}
        ]
        
        parallel_groups = planner.identify_parallel_steps(plan)
        assert len(parallel_groups[0]) == 2  # Steps 1 and 2 can run in parallel
    
    def test_plan_serialization(self, planner):
        """Test serializing plan to JSON."""
        plan = [
            {"step": 1, "action": "search", "description": "Search"},
            {"step": 2, "action": "analyze", "description": "Analyze"}
        ]
        
        serialized = planner.serialize_plan(plan)
        assert isinstance(serialized, str)
        
        deserialized = planner.deserialize_plan(serialized)
        assert deserialized == plan
    
    @pytest.mark.parametrize("task,expected_steps", [
        ("Send an email", 1),
        ("Search and summarize", 2),
        ("Read file, analyze, and report", 3)
    ])
    @pytest.mark.asyncio
    async def test_plan_complexity(self, planner, mock_llm, task, expected_steps):
        """Test plans of varying complexity."""
        mock_llm.generate.return_value = {
            "plan": [{"step": i, "action": f"action_{i}"} for i in range(1, expected_steps + 1)],
            "reasoning": "Generated plan"
        }
        
        with patch.object(planner, 'llm', mock_llm):
            plan = await planner.create_plan(task)
            assert len(plan) == expected_steps