"""
Mock LLM service for testing
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
import time
import random
import json


@dataclass
class MockLLMResponse:
    """Mock LLM response object"""
    content: str
    tokens_used: int
    latency_ms: float
    model: str = "mock-gpt-4"
    finish_reason: str = "stop"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "model": self.model,
            "finish_reason": self.finish_reason
        }


class MockLLMService:
    """Mock LLM service for testing"""
    
    def __init__(
        self,
        base_latency_ms: float = 500,
        latency_variance: float = 200,
        failure_rate: float = 0.0,
        token_rate: int = 100  # tokens per second
    ):
        """
        Initialize mock LLM service
        
        Args:
            base_latency_ms: Base response latency in milliseconds
            latency_variance: Random variance in latency
            failure_rate: Probability of request failure (0.0 to 1.0)
            token_rate: Token generation rate
        """
        self.base_latency_ms = base_latency_ms
        self.latency_variance = latency_variance
        self.failure_rate = failure_rate
        self.token_rate = token_rate
        
        # Response templates
        self.response_templates = {
            "plan": self._generate_plan_response,
            "summary": self._generate_summary_response,
            "prioritize": self._generate_priority_response,
            "default": self._generate_default_response
        }
        
        # Call tracking
        self.call_count = 0
        self.total_tokens = 0
        self.call_history: List[Dict[str, Any]] = []
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> MockLLMResponse:
        """
        Generate a mock LLM response
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            MockLLMResponse object
            
        Raises:
            Exception: If failure rate triggers
        """
        self.call_count += 1
        
        # Simulate failure
        if random.random() < self.failure_rate:
            raise Exception("Mock LLM service error: Random failure triggered")
        
        # Calculate latency
        latency = self.base_latency_ms + random.uniform(
            -self.latency_variance,
            self.latency_variance
        )
        
        # Simulate processing time
        time.sleep(latency / 1000)
        
        # Determine response type from prompt
        response_type = self._detect_response_type(prompt)
        
        # Generate response content
        generator = self.response_templates.get(
            response_type,
            self.response_templates["default"]
        )
        content = generator(prompt, max_tokens)
        
        # Calculate tokens (roughly based on content length)
        tokens_used = min(len(content.split()) * 1.3, max_tokens)
        tokens_used = int(tokens_used)
        
        self.total_tokens += tokens_used
        
        # Create response
        response = MockLLMResponse(
            content=content,
            tokens_used=tokens_used,
            latency_ms=latency
        )
        
        # Track call
        self.call_history.append({
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response": response.to_dict(),
            "timestamp": time.time()
        })
        
        return response
    
    async def generate_async(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> MockLLMResponse:
        """Async version of generate"""
        import asyncio
        
        # Simulate async behavior
        latency = self.base_latency_ms + random.uniform(
            -self.latency_variance,
            self.latency_variance
        )
        await asyncio.sleep(latency / 1000)
        
        # Use synchronous logic
        return self.generate(prompt, max_tokens, temperature, **kwargs)
    
    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 500,
        **kwargs
    ):
        """
        Generate streaming response
        
        Yields:
            Chunks of response content
        """
        response_type = self._detect_response_type(prompt)
        generator = self.response_templates.get(
            response_type,
            self.response_templates["default"]
        )
        
        full_content = generator(prompt, max_tokens)
        words = full_content.split()
        
        # Stream word by word
        for word in words:
            time.sleep(0.01)  # Simulate streaming delay
            yield word + " "
    
    def set_custom_response(
        self,
        trigger: str,
        response: str,
        tokens: int = None
    ):
        """
        Set a custom response for specific prompts
        
        Args:
            trigger: String to match in prompt
            response: Response to return
            tokens: Token count (auto-calculated if None)
        """
        if not hasattr(self, 'custom_responses'):
            self.custom_responses = {}
        
        self.custom_responses[trigger] = {
            "response": response,
            "tokens": tokens or int(len(response.split()) * 1.3)
        }
    
    def reset_stats(self):
        """Reset call tracking statistics"""
        self.call_count = 0
        self.total_tokens = 0
        self.call_history = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        avg_latency = (
            sum(call["response"]["latency_ms"] for call in self.call_history)
            / len(self.call_history)
            if self.call_history else 0
        )
        
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "average_latency_ms": avg_latency,
            "average_tokens_per_call": (
                self.total_tokens / self.call_count if self.call_count > 0 else 0
            )
        }
    
    def _detect_response_type(self, prompt: str) -> str:
        """Detect the type of response needed from prompt"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["plan", "schedule", "organize"]):
            return "plan"
        elif any(word in prompt_lower for word in ["summarize", "summary", "recap"]):
            return "summary"
        elif any(word in prompt_lower for word in ["prioritize", "priority", "important"]):
            return "prioritize"
        else:
            return "default"
    
    def _generate_plan_response(self, prompt: str, max_tokens: int) -> str:
        """Generate a plan-type response"""
        return """Based on your calendar and priorities, here's your optimized daily plan:

Morning (9:00 AM - 12:00 PM):
- Start with email triage and respond to urgent messages
- Deep work session: Focus on Q1 planning document
- Brief team standup meeting

Afternoon (1:00 PM - 5:00 PM):
- Client demo preparation
- 1:1 meeting with manager
- Sprint review and planning

Key priorities for today:
1. Complete Q1 objectives document
2. Prepare client demo materials
3. Review sprint deliverables

Time management tip: Block 2 hours for deep work on Q1 planning before meetings begin."""
    
    def _generate_summary_response(self, prompt: str, max_tokens: int) -> str:
        """Generate a summary-type response"""
        return """Summary of your day:

You have 8 calendar events scheduled, including 3 high-priority meetings. 
Your inbox contains 12 unread emails, with 3 marked as urgent.

Top action items:
- Respond to boss's email about Q1 planning
- Prepare materials for client demo
- Review sprint deliverables before team meeting

Estimated workload: High
Recommended focus: Q1 planning and client preparation"""
    
    def _generate_priority_response(self, prompt: str, max_tokens: int) -> str:
        """Generate a priority-type response"""
        return """Priority ranking for your tasks:

HIGH PRIORITY:
1. Q1 Planning Document - Due this week, requested by management
2. Client Demo Preparation - Meeting scheduled for tomorrow
3. Urgent email responses - Time-sensitive communications

MEDIUM PRIORITY:
4. Sprint review preparation
5. Team standup attendance
6. Benefits enrollment

LOW PRIORITY:
7. General email cleanup
8. Optional training session
9. Office supplies request

Recommendation: Focus on top 3 items today, defer low priority to later this week."""
    
    def _generate_default_response(self, prompt: str, max_tokens: int) -> str:
        """Generate a default response"""
        # Check for custom responses
        if hasattr(self, 'custom_responses'):
            for trigger, data in self.custom_responses.items():
                if trigger.lower() in prompt.lower():
                    return data["response"]
        
        return f"""I understand you're asking about: {prompt[:100]}

Based on the available information, I can help you with that. Here are some key points to consider:

1. Review the relevant context and background
2. Analyze the current situation and constraints
3. Identify potential solutions or next steps
4. Make a decision based on priorities and resources

Would you like me to elaborate on any specific aspect?"""


class MockLLMWithTools(MockLLMService):
    """Mock LLM service with tool calling support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_tools = {}
        self.tool_call_history: List[Dict[str, Any]] = []
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Register a tool that the LLM can call"""
        self.available_tools[name] = {
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def generate_with_tools(
        self,
        prompt: str,
        tools: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response with tool calling
        
        Returns:
            Dict with 'response' and optional 'tool_calls'
        """
        # Decide whether to use a tool (30% chance)
        use_tool = random.random() < 0.3 and tools
        
        result = {
            "response": self.generate(prompt, **kwargs)
        }
        
        if use_tool and tools:
            # Pick a random tool
            tool_name = random.choice(tools)
            if tool_name in self.available_tools:
                tool_call = {
                    "tool": tool_name,
                    "arguments": self._generate_tool_args(tool_name),
                    "call_id": f"call_{len(self.tool_call_history)}"
                }
                
                self.tool_call_history.append(tool_call)
                result["tool_calls"] = [tool_call]
        
        return result
    
    def _generate_tool_args(self, tool_name: str) -> Dict[str, Any]:
        """Generate mock arguments for a tool call"""
        # Simple mock arguments
        common_args = {
            "email_fetch": {"limit": 10, "unread_only": False},
            "calendar_query": {"days": 7},
            "task_create": {"title": "Mock task", "priority": "medium"},
            "search": {"query": "test query"}
        }
        
        return common_args.get(tool_name, {})
