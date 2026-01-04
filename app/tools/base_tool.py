"""
Base Tool Class
Abstract base class that all tools must inherit from
Ensures consistent interface and behavior
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

from app.schemas.tool_schema import (
    ToolInput,
    ToolResult,
    ToolCapability
)
from app.utils.logger import get_logger
from app.utils.validators import ToolValidator

logger = get_logger("tools.base")


class BaseTool(ABC):
    """
    Abstract base class for all tools
    
    All tools must:
    1. Inherit from this class
    2. Implement execute() method
    3. Define capabilities in get_capability()
    4. Handle errors gracefully
    5. Return structured ToolResult
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize tool
        
        Args:
            name: Tool name (unique identifier)
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"tools.{name}")
        self.execution_count = 0
        self.error_count = 0
        self.total_duration_ms = 0.0
    
    @abstractmethod
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """
        Execute the tool
        Must be implemented by subclasses
        
        Args:
            tool_input: Validated tool input
            
        Returns:
            ToolResult with execution outcome
        """
        pass
    
    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """
        Get tool capability description
        Must be implemented by subclasses
        
        Returns:
            ToolCapability describing what this tool can do
        """
        pass
    
    def run(self, tool_input: ToolInput) -> ToolResult:
        """
        Main entry point - wraps execute() with common logic
        
        Args:
            tool_input: Tool input
            
        Returns:
            ToolResult
        """
        start_time = time.time()
        
        self.logger.info(
            "Tool execution started",
            action=tool_input.action,
            params=tool_input.params
        )
        
        try:
            # Validate input
            validation = ToolValidator.validate_tool_input(self.name, tool_input)
            if not validation:
                return ToolResult(
                    success=False,
                    error=f"Validation failed: {validation.errors}",
                    error_type="validation",
                    executed_at=datetime.now()
                )
            
            # Execute tool
            result = self.execute(tool_input)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            
            # Update metrics
            self.execution_count += 1
            self.total_duration_ms += duration_ms
            
            if not result.success:
                self.error_count += 1
            
            # Add tool metadata
            result.add_metadata("tool_name", self.name)
            result.add_metadata("execution_count", self.execution_count)
            
            self.logger.info(
                "Tool execution completed",
                success=result.success,
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.error_count += 1
            
            self.logger.error(
                "Tool execution failed",
                error=str(e),
                exc_info=True
            )
            
            return ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                error_type="internal_error",
                duration_ms=duration_ms,
                executed_at=datetime.now()
            )
    
    def supports_action(self, action: str) -> bool:
        """
        Check if tool supports an action
        
        Args:
            action: Action name
            
        Returns:
            True if supported
        """
        capability = self.get_capability()
        return action in capability.supported_actions
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get tool execution metrics
        
        Returns:
            Metrics dictionary
        """
        avg_duration = (
            self.total_duration_ms / self.execution_count
            if self.execution_count > 0
            else 0.0
        )
        
        error_rate = (
            self.error_count / self.execution_count * 100
            if self.execution_count > 0
            else 0.0
        )
        
        return {
            "tool_name": self.name,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "average_duration_ms": avg_duration,
            "total_duration_ms": self.total_duration_ms
        }
    
    def reset_metrics(self):
        """Reset tool metrics"""
        self.execution_count = 0
        self.error_count = 0
        self.total_duration_ms = 0.0
    
    def health_check(self) -> bool:
        """
        Check if tool is healthy and ready to use
        Override in subclasses for specific checks
        
        Returns:
            True if healthy
        """
        # Default: always healthy
        # Subclasses can override to check API connectivity, etc.
        return True
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"executions={self.execution_count}, "
            f"errors={self.error_count})"
        )


class MockTool(BaseTool):
    """
    Mock tool for testing
    Can simulate success or failure
    """
    
    def __init__(
        self,
        name: str = "mock_tool",
        description: str = "Mock tool for testing",
        should_fail: bool = False,
        delay_ms: float = 0.0
    ):
        super().__init__(name, description)
        self.should_fail = should_fail
        self.delay_ms = delay_ms
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute mock tool"""
        # Simulate delay
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000)
        
        if self.should_fail:
            return ToolResult(
                success=False,
                error="Mock failure",
                error_type="mock_error"
            )
        
        return ToolResult(
            success=True,
            data={
                "action": tool_input.action,
                "params": tool_input.params,
                "mock": True,
                "message": "Mock execution successful"
            }
        )
    
    def get_capability(self) -> ToolCapability:
        """Get mock tool capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=["test", "mock", "simulate"],
            required_params={},
            optional_params={},
            requires_auth=False,
            examples=[]
        )


if __name__ == "__main__":
    """Test base tool"""
    
    print("🔧 Testing BaseTool...")
    
    # Create mock tool
    tool = MockTool(name="test_tool", delay_ms=100)
    
    # Test successful execution
    tool_input = ToolInput(
        action="test",
        params={"test_param": "value"}
    )
    
    result = tool.run(tool_input)
    
    print(f"\n✅ Successful execution:")
    print(f"   Success: {result.success}")
    print(f"   Duration: {result.duration_ms:.2f}ms")
    print(f"   Data: {result.data}")
    
    # Test failed execution
    failing_tool = MockTool(name="failing_tool", should_fail=True)
    result = failing_tool.run(tool_input)
    
    print(f"\n❌ Failed execution:")
    print(f"   Success: {result.success}")
    print(f"   Error: {result.error}")
    
    # Test metrics
    print(f"\n📊 Tool metrics:")
    metrics = tool.get_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # Test capability
    print(f"\n🔍 Tool capability:")
    capability = tool.get_capability()
    print(f"   Name: {capability.name}")
    print(f"   Actions: {capability.supported_actions}")
    
    print("\n✅ BaseTool test complete")