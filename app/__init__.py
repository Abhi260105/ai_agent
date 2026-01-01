"""
AI Agent Package
Autonomous Task-Executing AI Agent with LangGraph
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import key components for easy access
from app.config import config
from app.utils.logger import get_logger

# Package metadata
__all__ = [
    "config",
    "get_logger",
    "__version__",
]

# Initialize logging when package is imported
logger = get_logger("app")
logger.info(
    "AI Agent package initialized",
    version=__version__,
    environment=config.dev.environment
)