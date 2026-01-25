"""
Evaluator - Evaluates execution results and quality
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluates task execution results and quality."""
    
    def __init__(self, llm_service=None):
        """
        Initialize evaluator.
        
        Args:
            llm_service: LLM service for quality assessment
        """
        self.llm = llm_service
    
    async def evaluate_result(
        self,
        result: Dict[str, Any],
        goal: str,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate execution result.
        
        Args:
            result: Execution result
            goal: Original goal/task
            expected_output: Expected output (optional)
            
        Returns:
            Evaluation metrics
        """
        logger.info("Evaluating execution result")
        
        evaluation = {
            'success': result.get('status') == 'success',
            'goal_achieved': False,
            'score': 0.0,
            'quality': 'unknown'
        }
        
        # Calculate success metrics
        steps = result.get('steps', [])
        if steps:
            success_rate = self.calculate_success_rate(steps)
            evaluation['success_rate'] = success_rate
            evaluation['completion_rate'] = success_rate
        
        # Determine if goal was achieved
        evaluation['goal_achieved'] = result.get('status') == 'success'
        
        # Calculate score
        score = 0.0
        
        if evaluation['success']:
            score = 0.8  # Base score for success
            
            # Bonus for high success rate
            if evaluation.get('success_rate', 0) > 0.9:
                score += 0.1
            
            # Bonus for efficiency
            duration = result.get('duration', 0)
            if duration > 0 and duration < 30:  # Fast execution
                score += 0.1
        else:
            score = 0.3  # Partial credit for attempt
        
        evaluation['score'] = min(score, 1.0)
        
        # Determine quality level
        if score >= 0.9:
            evaluation['quality'] = 'excellent'
        elif score >= 0.7:
            evaluation['quality'] = 'good'
        elif score >= 0.5:
            evaluation['quality'] = 'acceptable'
        else:
            evaluation['quality'] = 'poor'
        
        # Identify failure points if failed
        if not evaluation['success']:
            evaluation['failure_points'] = self.identify_failure_points(result)
        
        # Get LLM assessment if available
        if self.llm and result.get('result'):
            llm_eval = await self.evaluate_with_llm(result, goal)
            evaluation['llm_judgment'] = llm_eval.get('assessment')
            evaluation['reasoning'] = llm_eval.get('reasoning')
        
        return evaluation
    
    def calculate_success_rate(self, steps: List[Dict]) -> float:
        """Calculate success rate from steps."""
        if not steps:
            return 0.0
        
        successful = sum(1 for step in steps if step.get('status') == 'success')
        return successful / len(steps)
    
    def identify_failure_points(self, result: Dict) -> List[Dict]:
        """Identify where execution failed."""
        failure_points = []
        
        for step in result.get('steps', []):
            if step.get('status') in ['error', 'timeout', 'failed']:
                failure_points.append({
                    'step': step.get('step'),
                    'action': step.get('action'),
                    'error': step.get('error'),
                    'status': step.get('status')
                })
        
        return failure_points
    
    async def evaluate_with_llm(
        self,
        result: Dict,
        goal: str
    ) -> Dict[str, Any]:
        """Use LLM to assess quality."""
        if not self.llm:
            return {}
        
        prompt = f"""
Evaluate the quality of this task execution:

Goal: {goal}
Result: {result.get('result', 'No result')}
Status: {result.get('status')}

Provide an assessment of quality (high_quality, medium_quality, low_quality) and reasoning.
Return as JSON with 'assessment' and 'reasoning' fields.
"""
        
        try:
            response = await self.llm.generate(prompt, temperature=0.3)
            content = response.get('content', '{}')
            
            # Parse response
            import json
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            
            assessment = json.loads(content)
            
            # Calculate score from assessment
            score_map = {
                'high_quality': 0.9,
                'medium_quality': 0.7,
                'low_quality': 0.4
            }
            
            assessment['score'] = score_map.get(
                assessment.get('assessment', 'medium_quality'),
                0.5
            )
            
            return assessment
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed: {str(e)}")
            return {}
    
    def compare_outputs(self, expected: str, actual: str) -> float:
        """Compare expected vs actual output."""
        if not expected or not actual:
            return 0.0
        
        # Simple word overlap similarity
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(expected_words & actual_words)
        similarity = overlap / len(expected_words)
        
        return similarity
    
    async def evaluate_efficiency(
        self,
        result: Dict,
        expected_duration: float = None
    ) -> Dict[str, Any]:
        """Evaluate execution efficiency."""
        efficiency = {}
        
        duration = result.get('duration', 0)
        
        if expected_duration:
            efficiency['time_efficiency'] = min(
                expected_duration / duration if duration > 0 else 0,
                1.0
            )
        
        # Check for retries
        retries = result.get('retries', 0)
        efficiency['retry_penalty'] = max(1.0 - (retries * 0.1), 0.5)
        
        # Overall efficiency score
        efficiency['score'] = (
            efficiency.get('time_efficiency', 0.8) *
            efficiency['retry_penalty']
        )
        
        return efficiency
    
    def check_goal_satisfaction(
        self,
        goal: str,
        result: Dict
    ) -> bool:
        """Check if goal was satisfied."""
        # Simple check: if status is success, goal is satisfied
        return result.get('status') == 'success'
    
    def detect_inconsistencies(self, result: Dict) -> List[str]:
        """Detect inconsistencies in results."""
        issues = []
        
        # Check for mismatched data
        if 'actual_recipients' in result and 'recipients' in result:
            if result['actual_recipients'] != result.get('recipients'):
                issues.append("Recipient count mismatch")
        
        return issues
    
    async def suggest_improvements(
        self,
        result: Dict
    ) -> List[str]:
        """Suggest improvements for failed execution."""
        suggestions = []
        
        failure_points = self.identify_failure_points(result)
        
        for failure in failure_points:
            if 'timeout' in failure.get('status', ''):
                suggestions.append(f"Increase timeout for step {failure['step']}")
            elif 'error' in failure.get('status', ''):
                suggestions.append(f"Check {failure['action']} parameters")
        
        if result.get('status') == 'failed':
            suggestions.append("Consider alternative approach or tools")
        
        return suggestions
    
    def calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score."""
        weights = {
            'completeness': 0.3,
            'correctness': 0.3,
            'efficiency': 0.2,
            'user_satisfaction': 0.2
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
        
        return min(score, 1.0)
    
    async def evaluate_with_feedback(
        self,
        result: Dict,
        user_feedback: Dict
    ) -> Dict[str, Any]:
        """Incorporate user feedback into evaluation."""
        evaluation = await self.evaluate_result(result, "")
        
        evaluation['user_rating'] = user_feedback.get('rating', 0)
        evaluation['user_comments'] = user_feedback.get('comments', '')
        evaluation['feedback_incorporated'] = True
        
        # Adjust score based on feedback
        if user_feedback.get('rating'):
            feedback_score = user_feedback['rating'] / 5.0
            evaluation['score'] = (evaluation['score'] + feedback_score) / 2
        
        return evaluation
    
    def benchmark(
        self,
        current_result: Dict,
        baseline: Dict
    ) -> Dict[str, Any]:
        """Benchmark against baseline."""
        comparison = {}
        
        # Duration improvement
        if 'duration' in current_result and 'duration' in baseline:
            improvement = baseline['duration'] - current_result['duration']
            comparison['duration_improvement'] = improvement
        
        # Success rate improvement
        if 'success_rate' in current_result and 'success_rate' in baseline:
            improvement = current_result['success_rate'] - baseline['success_rate']
            comparison['success_rate_improvement'] = improvement
        
        return comparison
    
    def identify_bottlenecks(
        self,
        execution_trace: List[Dict]
    ) -> List[Dict]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Find steps taking longest
        sorted_steps = sorted(
            execution_trace,
            key=lambda x: x.get('duration', 0),
            reverse=True
        )
        
        # Top 20% slowest steps are bottlenecks
        threshold = len(sorted_steps) // 5
        
        for step in sorted_steps[:max(1, threshold)]:
            bottlenecks.append({
                'step': step.get('step'),
                'duration': step.get('duration'),
                'action': step.get('action')
            })
        
        return bottlenecks
    
    def assign_grade(self, result: Dict) -> str:
        """Assign letter grade to result."""
        completion_rate = result.get('completion_rate', 0)
        
        if completion_rate >= 0.9:
            return 'A'
        elif completion_rate >= 0.8:
            return 'B'
        elif completion_rate >= 0.7:
            return 'C'
        elif completion_rate >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def evaluate_recovery(self, result: Dict) -> float:
        """Evaluate error recovery effectiveness."""
        if not result.get('initial_failure'):
            return 0.0
        
        if result.get('recovery_successful'):
            return 0.8  # Good recovery
        elif result.get('recovery_attempted'):
            return 0.4  # Attempted but failed
        else:
            return 0.0  # No recovery attempt