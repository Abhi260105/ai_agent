"""
Tool Registry
Central registry for all available tools
Manages tool discovery, selection, and health monitoring
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolCapability
from app.utils.logger import get_logger

logger = get_logger("tools.registry")


class ToolRegistry:
    """
    Central registry for all tools
    
    Features:
    - Dynamic tool registration
    - Tool discovery by name or capability
    - Health monitoring
    - Usage statistics
    - Tool selection logic
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._capabilities: Dict[str, ToolCapability] = {}
        self.logger = logger
    
    def register(self, tool: BaseTool):
        """
        Register a tool
        
        Args:
            tool: Tool instance to register
        """
        if tool.name in self._tools:
            self.logger.warning(
                f"Tool '{tool.name}' already registered, replacing"
            )
        
        self._tools[tool.name] = tool
        self._capabilities[tool.name] = tool.get_capability()
        
        self.logger.info(
            "Tool registered",
            tool_name=tool.name,
            actions=tool.get_capability().supported_actions
        )
    
    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if unregistered
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._capabilities[tool_name]
            self.logger.info("Tool unregistered", tool_name=tool_name)
            return True
        return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get tool by name
        
        Args:
            tool_name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self._tools.get(tool_name)
    
    def get_capability(self, tool_name: str) -> Optional[ToolCapability]:
        """
        Get tool capability
        
        Args:
            tool_name: Tool name
            
        Returns:
            ToolCapability or None
        """
        return self._capabilities.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def list_capabilities(self) -> Dict[str, ToolCapability]:
        """
        Get all tool capabilities
        
        Returns:
            Dict mapping tool name to capability
        """
        return self._capabilities.copy()
    
    def find_tools_for_action(self, action: str) -> List[str]:
        """
        Find tools that support an action
        
        Args:
            action: Action name
            
        Returns:
            List of tool names
        """
        matching_tools = []
        
        for tool_name, capability in self._capabilities.items():
            if action in capability.supported_actions:
                matching_tools.append(tool_name)
        
        return matching_tools
    
    def select_tool_for_action(
        self,
        action: str,
        prefer_tools: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Select best tool for an action
        
        Args:
            action: Action to perform
            prefer_tools: Preferred tools (in order)
            
        Returns:
            Selected tool name or None
        """
        matching_tools = self.find_tools_for_action(action)
        
        if not matching_tools:
            return None
        
        # If preferences provided, use first matching
        if prefer_tools:
            for pref in prefer_tools:
                if pref in matching_tools:
                    return pref
        
        # Otherwise return first matching tool
        return matching_tools[0]
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all tools
        
        Returns:
            Dict mapping tool name to health status
        """
        health_status = {}
        
        for tool_name, tool in self._tools.items():
            try:
                is_healthy = tool.health_check()
                health_status[tool_name] = is_healthy
                
                if not is_healthy:
                    self.logger.warning(
                        "Tool health check failed",
                        tool_name=tool_name
                    )
            except Exception as e:
                self.logger.error(
                    "Tool health check error",
                    tool_name=tool_name,
                    error=str(e)
                )
                health_status[tool_name] = False
        
        return health_status
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all tools
        
        Returns:
            Dict mapping tool name to metrics
        """
        all_metrics = {}
        
        for tool_name, tool in self._tools.items():
            all_metrics[tool_name] = tool.get_metrics()
        
        return all_metrics
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics
        
        Returns:
            Statistics dictionary
        """
        total_executions = sum(
            tool.execution_count for tool in self._tools.values()
        )
        
        total_errors = sum(
            tool.error_count for tool in self._tools.values()
        )
        
        return {
            "total_tools": len(self._tools),
            "total_executions": total_executions,
            "total_errors": total_errors,
            "error_rate_percent": (
                total_errors / total_executions * 100
                if total_executions > 0
                else 0.0
            ),
            "tools": self.list_tools()
        }
    
    def reset_all_metrics(self):
        """Reset metrics for all tools"""
        for tool in self._tools.values():
            tool.reset_metrics()
        
        self.logger.info("All tool metrics reset")
    
    def __len__(self) -> int:
        """Number of registered tools"""
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered"""
        return tool_name in self._tools
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ToolRegistry(tools={len(self._tools)}, "
            f"total_executions={sum(t.execution_count for t in self._tools.values())})"
        )


# Global tool registry instance
tool_registry = ToolRegistry()


def register_all_tools():
    """
    Register all available tools
    Called on application startup
    """
    logger.info("Registering all tools...")
    
    try:
        # Import and register tools
        # (Tools will be registered as they're created in Phase 3)
        
        from app.tools.base_tool import MockTool
        
        # Register mock tool for testing
        mock_tool = MockTool(name="mock_tool")
        tool_registry.register(mock_tool)
        
        logger.info(
            "Tools registered",
            count=len(tool_registry),
            tools=tool_registry.list_tools()
        )
        
    except Exception as e:
        logger.error("Tool registration failed", error=str(e))
        raise


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """
    Convenience function to get a tool
    
    Args:
        tool_name: Tool name
        
    Returns:
        Tool instance or None
    """
    return tool_registry.get(tool_name)


if __name__ == "__main__":
    """Test tool registry"""
    from app.tools.base_tool import MockTool
    
    print("📋 Testing Tool Registry...")
    
    # Create registry
    registry = ToolRegistry()
    
    # Register some mock tools
    tool1 = MockTool(name="tool1", description="First tool")
    tool2 = MockTool(name="tool2", description="Second tool")
    
    registry.register(tool1)
    registry.register(tool2)
    
    print(f"\n✅ Registered tools:")
    for tool_name in registry.list_tools():
        print(f"   - {tool_name}")
    
    # Test tool retrieval
    retrieved = registry.get("tool1")
    print(f"\n🔍 Retrieved tool: {retrieved}")
    
    # Test action lookup
    matching = registry.find_tools_for_action("test")
    print(f"\n🎯 Tools supporting 'test': {matching}")
    
    # Test tool selection
    selected = registry.select_tool_for_action("test")
    print(f"\n⭐ Selected tool: {selected}")
    
    # Test health check
    health = registry.health_check_all()
    print(f"\n💚 Health status:")
    for tool, status in health.items():
        print(f"   {tool}: {'✓' if status else '✗'}")
    
    # Test statistics
    stats = registry.get_statistics()
    print(f"\n📊 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Tool registry test complete")