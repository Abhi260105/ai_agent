"""
Unit tests for Evaluator component.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestEvaluator:
    """Test suite for the Evaluator component."""
    
    @pytest.fixture
    def evaluator(self):
        """Create an Evaluator instance for testing."""
        from app.core.evaluator import Evaluator
        return Evaluator()
    
    @pytest.fixture
    def successful_result(self):
        """Sample successful execution result."""
        return {
            "status": "success",
            "result": "Task completed successfully",
            "steps": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "success"}
            ]
        }
    
    @pytest.fixture
    def failed_result(self):
        """Sample failed execution result."""
        return {
            "status": "failed",
            "error": "Step 2 failed",
            "steps": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "failed", "error": "Tool error"}
            ]
        }
    
    def test_evaluator_initialization(self, evaluator):
        """Test evaluator initializes correctly."""
        assert evaluator is not None
        assert hasattr(evaluator, 'evaluate_result')
        assert hasattr(evaluator, 'evaluate_plan_success')
    
    @pytest.mark.asyncio
    async def test_evaluate_successful_result(self, evaluator, successful_result):
        """Test evaluating a successful result."""
        evaluation = await evaluator.evaluate_result(successful_result, goal="Complete task")
        
        assert evaluation['success'] is True
        assert evaluation['goal_achieved'] is True
        assert evaluation['score'] > 0.7
    
    @pytest.mark.asyncio
    async def test_evaluate_failed_result(self, evaluator, failed_result):
        """Test evaluating a failed result."""
        evaluation = await evaluator.evaluate_result(failed_result, goal="Complete task")
        
        assert evaluation['success'] is False
        assert evaluation['score'] < 0.5
        assert 'error_analysis' in evaluation
    
    @pytest.mark.asyncio
    async def test_evaluate_partial_success(self, evaluator):
        """Test evaluating partial success."""
        partial_result = {
            "status": "partial",
            "result": "2 out of 3 tasks completed",
            "steps": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "success"},
                {"step": 3, "status": "failed"}
            ]
        }
        
        evaluation = await evaluator.evaluate_result(partial_result, goal="Complete all tasks")
        
        assert 0.3 < evaluation['score'] < 0.8
        assert evaluation['completion_rate'] == pytest.approx(2/3, 0.1)
    
    def test_calculate_success_rate(self, evaluator):
        """Test calculating success rate."""
        steps = [
            {"status": "success"},
            {"status": "success"},
            {"status": "failed"},
            {"status": "success"}
        ]
        
        success_rate = evaluator.calculate_success_rate(steps)
        assert success_rate == 0.75
    
    def test_identify_failure_points(self, evaluator, failed_result):
        """Test identifying where execution failed."""
        failure_points = evaluator.identify_failure_points(failed_result)
        
        assert len(failure_points) > 0
        assert failure_points[0]['step'] == 2
        assert 'error' in failure_points[0]
    
    @pytest.mark.asyncio
    async def test_evaluate_with_llm_judgment(self, evaluator):
        """Test using LLM for quality assessment."""
        result = {
            "status": "success",
            "result": "Email sent to team with quarterly report"
        }
        
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = {
            "assessment": "high_quality",
            "reasoning": "Task completed as requested",
            "score": 0.9
        }
        
        with patch.object(evaluator, 'llm', mock_llm):
            evaluation = await evaluator.evaluate_with_llm(
                result,
                goal="Send quarterly report to team"
            )
            
            assert evaluation['score'] >= 0.8
            assert evaluation['llm_judgment'] == "high_quality"
    
    def test_compare_expected_vs_actual(self, evaluator):
        """Test comparing expected output with actual result."""
        expected = "Report generated with 5 sections"
        actual = "Report generated with 5 sections and charts"
        
        similarity = evaluator.compare_outputs(expected, actual)
        assert similarity > 0.7
    
    @pytest.mark.asyncio
    async def test_evaluate_execution_efficiency(self, evaluator):
        """Test evaluating execution efficiency."""
        result = {
            "status": "success",
            "duration": 12.5,
            "steps": 3,
            "retries": 1
        }
        
        efficiency = await evaluator.evaluate_efficiency(
            result,
            expected_duration=15.0
        )
        
        assert efficiency['time_efficiency'] > 0.8
        assert efficiency['retry_penalty'] < 1.0
    
    def test_check_goal_satisfaction(self, evaluator):
        """Test checking if goal was satisfied."""
        goal = "Send email with attachment to john@example.com"
        
        successful_result = {
            "action": "send_email",
            "recipient": "john@example.com",
            "has_attachment": True
        }
        
        is_satisfied = evaluator.check_goal_satisfaction(goal, successful_result)
        assert is_satisfied is True
    
    def test_detect_hallucination(self, evaluator):
        """Test detecting hallucinated or incorrect information."""
        result = {
            "status": "success",
            "result": "Email sent to 50 recipients",
            "actual_recipients": 3
        }
        
        issues = evaluator.detect_inconsistencies(result)
        assert len(issues) > 0
        assert any('recipient' in issue.lower() for issue in issues)
    
    @pytest.mark.asyncio
    async def test_suggest_improvements(self, evaluator, failed_result):
        """Test generating improvement suggestions."""
        suggestions = await evaluator.suggest_improvements(failed_result)
        
        assert len(suggestions) > 0
        assert any('retry' in s.lower() or 'alternative' in s.lower() for s in suggestions)
    
    def test_calculate_quality_score(self, evaluator):
        """Test calculating overall quality score."""
        metrics = {
            'completeness': 0.9,
            'correctness': 0.85,
            'efficiency': 0.8,
            'user_satisfaction': 0.95
        }
        
        score = evaluator.calculate_quality_score(metrics)
        assert 0.0 <= score <= 1.0
        assert score > 0.8
    
    @pytest.mark.asyncio
    async def test_evaluate_with_user_feedback(self, evaluator):
        """Test incorporating user feedback into evaluation."""
        result = {"status": "success", "result": "Report generated"}
        user_feedback = {
            "rating": 4,
            "comments": "Good but missing some details"
        }
        
        evaluation = await evaluator.evaluate_with_feedback(result, user_feedback)
        
        assert 'user_rating' in evaluation
        assert evaluation['user_rating'] == 4
        assert 'feedback_incorporated' in evaluation
    
    def test_benchmark_against_baseline(self, evaluator):
        """Test benchmarking results against baseline."""
        current_result = {
            "duration": 10.5,
            "success_rate": 0.9,
            "quality_score": 0.85
        }
        
        baseline = {
            "duration": 15.0,
            "success_rate": 0.8,
            "quality_score": 0.75
        }
        
        comparison = evaluator.benchmark(current_result, baseline)
        
        assert comparison['duration_improvement'] > 0
        assert comparison['success_rate_improvement'] > 0
    
    @pytest.mark.asyncio
    async def test_identify_bottlenecks(self, evaluator):
        """Test identifying performance bottlenecks."""
        execution_trace = [
            {"step": 1, "duration": 2.0},
            {"step": 2, "duration": 15.0},  # Bottleneck
            {"step": 3, "duration": 1.5}
        ]
        
        bottlenecks = evaluator.identify_bottlenecks(execution_trace)
        
        assert len(bottlenecks) > 0
        assert bottlenecks[0]['step'] == 2
    
    @pytest.mark.parametrize("completion_rate,expected_grade", [
        (1.0, "A"),
        (0.9, "A"),
        (0.8, "B"),
        (0.7, "C"),
        (0.5, "D"),
        (0.3, "F")
    ])
    def test_grade_assignment(self, evaluator, completion_rate, expected_grade):
        """Test assigning letter grades to results."""
        result = {"completion_rate": completion_rate}
        grade = evaluator.assign_grade(result)
        assert grade == expected_grade
    
    def test_evaluate_error_recovery(self, evaluator):
        """Test evaluating error recovery attempts."""
        result = {
            "initial_failure": True,
            "recovery_attempted": True,
            "recovery_successful": True,
            "final_status": "success"
        }
        
        recovery_score = evaluator.evaluate_recovery(result)
        assert recovery_score > 0.5