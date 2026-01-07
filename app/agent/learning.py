"""
Learning Engine - Agent Learning System
Extracts patterns, analyzes performance, and optimizes strategies
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

from app.services.storage_service import storage_service
from app.agent.memory import memory_manager
from app.schemas.plan_schema import PlanSchema, StepSchema
from app.utils.logger import get_logger

logger = get_logger("agent.learning")


class LearningEngine:
    """
    Agent learning and optimization system
    
    Features:
    - Pattern extraction from past tasks
    - Success/failure analysis
    - Strategy optimization
    - Adaptive replanning
    - Knowledge graph building
    """
    
    def __init__(self):
        self.logger = logger
        self.storage = storage_service
        self.memory = memory_manager
        
        self.logger.info("Learning engine initialized")
    
    # =========================================================================
    # PATTERN EXTRACTION
    # =========================================================================
    
    def extract_patterns(
        self,
        min_occurrences: int = 3,
        min_success_rate: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Extract successful patterns from past tasks
        
        Args:
            min_occurrences: Minimum times pattern must occur
            min_success_rate: Minimum success rate
            
        Returns:
            List of extracted patterns
        """
        self.logger.info("Extracting patterns")
        
        # Get recent tasks
        tasks = self.storage.list_tasks(limit=100)
        
        # Group by goal similarity
        goal_groups = self._group_similar_goals(tasks)
        
        patterns = []
        for goal_type, task_list in goal_groups.items():
            if len(task_list) < min_occurrences:
                continue
            
            # Analyze pattern
            pattern = self._analyze_task_group(task_list)
            
            if pattern["success_rate"] >= min_success_rate:
                patterns.append({
                    "goal_type": goal_type,
                    "occurrences": len(task_list),
                    "success_rate": pattern["success_rate"],
                    "common_tools": pattern["common_tools"],
                    "common_steps": pattern["common_steps"],
                    "avg_duration": pattern["avg_duration"]
                })
        
        # Save patterns to memory
        for pattern in patterns:
            self.memory.store_success_pattern(pattern)
        
        self.logger.info(f"Extracted {len(patterns)} patterns")
        return patterns
    
    def _group_similar_goals(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group tasks by goal similarity"""
        groups = defaultdict(list)
        
        # Simple grouping by keywords
        keywords = ["email", "calendar", "meeting", "file", "search", "schedule"]
        
        for task in tasks:
            goal = task.get("user_goal", "").lower()
            
            # Find matching keyword
            matched = False
            for keyword in keywords:
                if keyword in goal:
                    groups[keyword].append(task)
                    matched = True
                    break
            
            if not matched:
                groups["general"].append(task)
        
        return groups
    
    def _analyze_task_group(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze group of similar tasks"""
        successful = [t for t in tasks if t.get("status") == "completed"]
        
        # Calculate success rate
        success_rate = len(successful) / len(tasks) if tasks else 0
        
        # Get common tools used
        all_tools = []
        for task in successful:
            # Get steps for this task
            steps = self.storage.get_task_steps(task["id"])
            all_tools.extend([s["tool_name"] for s in steps])
        
        common_tools = [
            tool for tool, count in Counter(all_tools).most_common(5)
        ]
        
        # Get common step patterns
        all_actions = []
        for task in successful:
            steps = self.storage.get_task_steps(task["id"])
            all_actions.extend([s["action"] for s in steps])
        
        common_steps = [
            action for action, count in Counter(all_actions).most_common(5)
        ]
        
        # Calculate average duration
        durations = [
            t.get("duration_seconds", 0)
            for t in successful
            if t.get("duration_seconds")
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "success_rate": success_rate,
            "common_tools": common_tools,
            "common_steps": common_steps,
            "avg_duration": avg_duration
        }
    
    # =========================================================================
    # FAILURE ANALYSIS
    # =========================================================================
    
    def analyze_failures(
        self,
        task_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze past failures to learn what to avoid
        
        Args:
            task_type: Specific task type to analyze
            days: Days to look back
            
        Returns:
            Failure analysis report
        """
        self.logger.info("Analyzing failures", task_type=task_type, days=days)
        
        # Get tool usage statistics
        tool_stats = self.storage.get_tool_statistics(days=days)
        
        # Identify problematic tools
        problematic_tools = []
        for tool, stats in tool_stats.items():
            if stats["success_rate"] < 70:  # Less than 70% success
                problematic_tools.append({
                    "tool": tool,
                    "success_rate": stats["success_rate"],
                    "total_calls": stats["total_calls"]
                })
        
        # Get common error patterns
        error_patterns = self._extract_error_patterns(days=days)
        
        # Generate insights
        insights = self._generate_failure_insights(
            problematic_tools,
            error_patterns
        )
        
        report = {
            "analysis_period_days": days,
            "task_type": task_type,
            "problematic_tools": problematic_tools,
            "common_errors": error_patterns,
            "insights": insights,
            "recommendations": self._generate_recommendations(insights)
        }
        
        self.logger.info(
            "Failure analysis complete",
            problematic_tools=len(problematic_tools),
            common_errors=len(error_patterns)
        )
        
        return report
    
    def _extract_error_patterns(self, days: int) -> List[Dict[str, Any]]:
        """Extract common error patterns"""
        # Query database for errors
        # Simplified implementation
        return [
            {
                "error_type": "timeout",
                "count": 5,
                "tools": ["web_search_tool"],
                "resolution_rate": 0.8
            },
            {
                "error_type": "authentication",
                "count": 3,
                "tools": ["email_tool", "calendar_tool"],
                "resolution_rate": 0.3
            }
        ]
    
    def _generate_failure_insights(
        self,
        problematic_tools: List[Dict],
        error_patterns: List[Dict]
    ) -> List[str]:
        """Generate insights from failure data"""
        insights = []
        
        # Tool-specific insights
        for tool in problematic_tools:
            if tool["success_rate"] < 50:
                insights.append(
                    f"{tool['tool']} has very low success rate ({tool['success_rate']:.1f}%), "
                    f"consider using alternative or fixing integration"
                )
        
        # Error pattern insights
        for pattern in error_patterns:
            if pattern["count"] > 10:
                insights.append(
                    f"{pattern['error_type']} errors are frequent ({pattern['count']} times), "
                    f"affecting {', '.join(pattern['tools'])}"
                )
        
        return insights
    
    def _generate_recommendations(self, insights: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for insight in insights:
            if "low success rate" in insight:
                recommendations.append(
                    "Review tool configuration and API credentials"
                )
            elif "timeout" in insight.lower():
                recommendations.append(
                    "Increase timeout values or optimize queries"
                )
            elif "authentication" in insight.lower():
                recommendations.append(
                    "Verify API keys and refresh OAuth tokens"
                )
        
        return list(set(recommendations))  # Remove duplicates
    
    # =========================================================================
    # STRATEGY OPTIMIZATION
    # =========================================================================
    
    def get_success_strategies(
        self,
        goal: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get successful strategies for a goal
        
        Args:
            goal: Goal description
            top_k: Number of strategies to return
            
        Returns:
            List of successful strategies
        """
        self.logger.debug("Getting success strategies", goal=goal)
        
        # Retrieve similar successful tasks
        similar_tasks = self.memory.retrieve_similar_tasks(
            query=goal,
            limit=top_k * 2
        )
        
        # Filter for successful tasks
        successful = [
            t for t in similar_tasks
            if t.get("memory_type") in ["task", "success"]
        ]
        
        # Extract strategies
        strategies = []
        for task in successful[:top_k]:
            strategy = {
                "approach": task.get("text", ""),
                "similarity": task.get("similarity", 0),
                "memory_type": task.get("memory_type"),
                "timestamp": task.get("timestamp")
            }
            strategies.append(strategy)
        
        return strategies
    
    def optimize_plan(
        self,
        plan: PlanSchema,
        past_performance: Dict[str, Any]
    ) -> PlanSchema:
        """
        Optimize plan based on past performance
        
        Args:
            plan: Original plan
            past_performance: Performance metrics
            
        Returns:
            Optimized plan
        """
        self.logger.info("Optimizing plan", plan_id=plan.id)
        
        optimized_steps = []
        
        for step in plan.steps:
            # Get tool performance
            tool_stats = self.storage.get_tool_statistics(
                tool_name=step.tool
            )
            
            # Adjust based on performance
            if step.tool in tool_stats:
                stats = tool_stats[step.tool]
                
                # Increase timeout if tool is slow
                if stats["avg_duration_ms"] > 5000:
                    step.timeout_seconds = max(
                        step.timeout_seconds,
                        int(stats["avg_duration_ms"] / 1000 * 1.5)
                    )
                
                # Increase retries if tool is unreliable
                if stats["success_rate"] < 80:
                    step.max_retries = min(step.max_retries + 1, 5)
            
            optimized_steps.append(step)
        
        plan.steps = optimized_steps
        return plan
    
    def adaptive_replan(
        self,
        failed_plan: PlanSchema,
        failure_context: Dict[str, Any]
    ) -> PlanSchema:
        """
        Create new plan by learning from failure
        
        Args:
            failed_plan: Plan that failed
            failure_context: Context about the failure
            
        Returns:
            New optimized plan
        """
        self.logger.info("Adaptive replanning", plan_id=failed_plan.id)
        
        # Analyze what went wrong
        failed_steps = failure_context.get("failed_steps", [])
        
        # Find alternative approaches
        alternatives = self._find_alternative_approaches(
            failed_plan.objective,
            failed_steps
        )
        
        # Create new plan with alternatives
        new_steps = []
        for step in failed_plan.steps:
            if step.id in failed_steps:
                # Replace with alternative
                alternative = self._select_best_alternative(
                    step,
                    alternatives
                )
                if alternative:
                    new_steps.append(alternative)
                else:
                    # Keep original but adjust parameters
                    step.max_retries = min(step.max_retries + 1, 5)
                    step.timeout_seconds = int(step.timeout_seconds * 1.5)
                    new_steps.append(step)
            else:
                new_steps.append(step)
        
        # Create new plan
        new_plan = PlanSchema(
            objective=failed_plan.objective,
            steps=new_steps,
            priority=failed_plan.priority,
            tags=failed_plan.tags + ["replanned"]
        )
        
        return new_plan
    
    def _find_alternative_approaches(
        self,
        objective: str,
        failed_steps: List[str]
    ) -> Dict[str, List[StepSchema]]:
        """Find alternative approaches for failed steps"""
        # Retrieve successful patterns
        patterns = self.memory.retrieve_success_patterns(
            goal_type=objective,
            limit=5
        )
        
        alternatives = {}
        # Extract alternative steps from patterns
        # Simplified implementation
        
        return alternatives
    
    def _select_best_alternative(
        self,
        failed_step: StepSchema,
        alternatives: Dict[str, List[StepSchema]]
    ) -> Optional[StepSchema]:
        """Select best alternative for a failed step"""
        # Simplified implementation
        return None
    
    # =========================================================================
    # KNOWLEDGE GRAPH
    # =========================================================================
    
    def build_knowledge_graph(self) -> Dict[str, Any]:
        """
        Build knowledge graph from learned patterns
        
        Returns:
            Knowledge graph structure
        """
        self.logger.info("Building knowledge graph")
        
        # Get all learned patterns
        patterns = self.storage.get_patterns()
        
        # Build nodes and edges
        nodes = []
        edges = []
        
        # Create nodes for tools
        tool_stats = self.storage.get_tool_statistics()
        for tool, stats in tool_stats.items():
            nodes.append({
                "id": f"tool:{tool}",
                "type": "tool",
                "name": tool,
                "success_rate": stats["success_rate"],
                "total_calls": stats["total_calls"]
            })
        
        # Create nodes for patterns
        for pattern in patterns:
            pattern_id = f"pattern:{pattern['id']}"
            nodes.append({
                "id": pattern_id,
                "type": "pattern",
                "pattern_type": pattern["pattern_type"],
                "confidence": pattern["confidence"]
            })
            
            # Create edges to tools
            pattern_data = pattern.get("pattern_data", {})
            tools = pattern_data.get("tools_used", [])
            for tool in tools:
                edges.append({
                    "source": pattern_id,
                    "target": f"tool:{tool}",
                    "type": "uses"
                })
        
        graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }
        
        self.logger.info(
            "Knowledge graph built",
            nodes=len(nodes),
            edges=len(edges)
        )
        
        return graph
    
    # =========================================================================
    # STATISTICS & INSIGHTS
    # =========================================================================
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        patterns = self.storage.get_patterns()
        tool_stats = self.storage.get_tool_statistics()
        
        return {
            "total_patterns": len(patterns),
            "high_confidence_patterns": len([
                p for p in patterns if p["confidence"] > 0.8
            ]),
            "tools_analyzed": len(tool_stats),
            "avg_tool_success_rate": sum(
                s["success_rate"] for s in tool_stats.values()
            ) / len(tool_stats) if tool_stats else 0
        }


# Global learning engine instance
learning_engine = LearningEngine()


if __name__ == "__main__":
    """Test learning engine"""
    print("🧠 Testing Learning Engine...")
    
    # Test pattern extraction
    print("\n🔍 Testing pattern extraction...")
    patterns = learning_engine.extract_patterns(
        min_occurrences=1,  # Low threshold for testing
        min_success_rate=0.5
    )
    print(f"   Patterns extracted: {len(patterns)}")
    
    # Test failure analysis
    print("\n❌ Testing failure analysis...")
    analysis = learning_engine.analyze_failures(days=30)
    print(f"   Problematic tools: {len(analysis['problematic_tools'])}")
    print(f"   Insights: {len(analysis['insights'])}")
    
    # Test success strategies
    print("\n✅ Testing success strategies...")
    strategies = learning_engine.get_success_strategies(
        goal="email task",
        top_k=3
    )
    print(f"   Strategies found: {len(strategies)}")
    
    # Test knowledge graph
    print("\n🕸️  Testing knowledge graph...")
    graph = learning_engine.build_knowledge_graph()
    print(f"   Nodes: {graph['metadata']['total_nodes']}")
    print(f"   Edges: {graph['metadata']['total_edges']}")
    
    # Test learning stats
    print("\n📊 Learning statistics:")
    stats = learning_engine.get_learning_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Learning engine test complete")