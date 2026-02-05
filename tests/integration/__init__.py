"""
Integration tests package for AI Agent System.

These tests verify that components work together correctly.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration

__all__ = []