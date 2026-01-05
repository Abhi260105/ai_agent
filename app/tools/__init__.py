"""
Tools Module
All tool implementations
"""

from app.tools.base_tool import BaseTool, MockTool
from app.tools.tool_registry import tool_registry, register_all_tools, get_tool
from app.tools.email_tool import EmailTool
from app.tools.calendar_tool import CalendarTool
from app.tools.file_tool import FileTool
from app.tools.web_search_tool import WebSearchTool
from app.tools.code_executor_tool import CodeExecutorTool
from app.tools.data_analysis_tool import DataAnalysisTool

__all__ = [
    # Base
    "BaseTool",
    "MockTool",
    
    # Registry
    "tool_registry",
    "register_all_tools",
    "get_tool",
    
    # Tools
    "EmailTool",
    "CalendarTool",
    "FileTool",
    "WebSearchTool",
    "CodeExecutorTool",
    "DataAnalysisTool",
]


def initialize_tools():
    """
    Initialize and register all tools
    Called on application startup
    """
    from app.config import config
    
    # Determine if using mock mode
    mock_mode = config.dev.enable_mock_tools
    
    # Email tool
    email_tool = EmailTool(mock_mode=mock_mode)
    tool_registry.register(email_tool)
    
    # Calendar tool
    calendar_tool = CalendarTool(mock_mode=mock_mode)
    tool_registry.register(calendar_tool)
    
    # File tool
    file_tool = FileTool()
    tool_registry.register(file_tool)
    
    # Web search tool
    search_tool = WebSearchTool(mock_mode=mock_mode)
    tool_registry.register(search_tool)
    
    # Code executor tool
    code_tool = CodeExecutorTool()
    tool_registry.register(code_tool)
    
    # Data analysis tool
    analysis_tool = DataAnalysisTool()
    tool_registry.register(analysis_tool)
    
    return tool_registry