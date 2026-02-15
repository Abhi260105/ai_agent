Tool Development Guide
Overview
This guide provides comprehensive instructions for developing, testing, and deploying tools within the system. Tools are modular components that extend system functionality.
Tool Architecture
Tool Structure
tools/
├── __init__.py
├── base_tool.py           # Abstract base class
├── my_tool/
│   ├── __init__.py
│   ├── tool.py            # Tool implementation
│   ├── config.py          # Configuration
│   ├── schema.py          # Input/output schemas
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_tool.py
│   └── README.md
Base Tool Interface
pythonfrom abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """
    Abstract base class for all tools.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = None
        self.description = None
        self.version = "1.0.0"
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.
        
        Args:
            input_data: Input parameters
            
        Returns:
            Result dictionary
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for input validation.
        """
        return {}
Creating a New Tool
Step 1: Define Tool Class
python# tools/email_sender/tool.py

from tools.base_tool import BaseTool
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText

class EmailSenderTool(BaseTool):
    """
    Tool for sending emails via SMTP.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "email_sender"
        self.description = "Send emails via SMTP"
        self.version = "1.0.0"
        
        # Initialize SMTP configuration
        self.smtp_host = config.get('smtp_host')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_pass = config.get('smtp_pass')
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            input_data: {
                'to': str or list,
                'subject': str,
                'body': str,
                'from': str (optional)
            }
            
        Returns:
            {
                'success': bool,
                'message_id': str,
                'error': str (if failed)
            }
        """
        if not self.validate_input(input_data):
            return {'success': False, 'error': 'Invalid input'}
        
        try:
            msg = MIMEText(input_data['body'])
            msg['Subject'] = input_data['subject']
            msg['From'] = input_data.get('from', self.smtp_user)
            msg['To'] = input_data['to']
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return {
                'success': True,
                'message_id': msg['Message-ID']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate email input.
        """
        required_fields = ['to', 'subject', 'body']
        return all(field in input_data for field in required_fields)
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema.
        """
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "format": "email"},
                "subject": {"type": "string", "minLength": 1},
                "body": {"type": "string"},
                "from": {"type": "string", "format": "email"}
            },
            "required": ["to", "subject", "body"]
        }
        Step 2: Create Configuration
python# tools/email_sender/config.py

DEFAULT_CONFIG = {
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 587,
    'timeout': 30,
    'max_retries': 3
}

REQUIRED_CONFIG = [
    'smtp_user',
    'smtp_pass'
]
Step 3: Write Tests
python# tools/email_sender/tests/test_tool.py

import pytest
from tools.email_sender.tool import EmailSenderTool

@pytest.fixture
def tool():
    config = {
        'smtp_host': 'smtp.example.com',
        'smtp_port': 587,
        'smtp_user': 'test@example.com',
        'smtp_pass': 'password123'
    }
    return EmailSenderTool(config)

def test_validate_input(tool):
    valid_input = {
        'to': 'recipient@example.com',
        'subject': 'Test Email',
        'body': 'This is a test'
    }
    assert tool.validate_input(valid_input) is True

def test_invalid_input(tool):
    invalid_input = {
        'subject': 'Test Email'
    }
    assert tool.validate_input(invalid_input) is False

def test_execute(tool, mocker):
    # Mock SMTP
    mock_smtp = mocker.patch('smtplib.SMTP')
    
    input_data = {
        'to': 'recipient@example.com',
        'subject': 'Test',
        'body': 'Test body'
    }
    
    result = tool.execute(input_data)
    assert result['success'] is True
Tool Registration
Register Tool in System
python# tools/__init__.py

from tools.email_sender.tool import EmailSenderTool
from tools.data_processor.tool import DataProcessorTool

REGISTERED_TOOLS = {
    'email_sender': EmailSenderTool,
    'data_processor': DataProcessorTool,
}

def get_tool(name: str, config: Dict[str, Any]):
    """
    Factory function to get tool instance.
    """
    if name not in REGISTERED_TOOLS:
        raise ValueError(f"Tool '{name}' not found")
    
    tool_class = REGISTERED_TOOLS[name]
    return tool_class(config)
Best Practices
1. Error Handling
pythondef execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Validate input
        if not self.validate_input(input_data):
            return self._error_response('Invalid input')
        
        # Execute logic
        result = self._process(input_data)
        
        # Return success
        return self._success_response(result)
        
    except ValidationError as e:
        return self._error_response(f'Validation error: {str(e)}')
    except ConnectionError as e:
        return self._error_response(f'Connection error: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return self._error_response('Internal server error')

def _success_response(self, data: Any) -> Dict[str, Any]:
    return {'success': True, 'data': data}

def _error_response(self, message: str) -> Dict[str, Any]:
    return {'success': False, 'error': message}
2. Configuration Management
pythonclass MyTool(BaseTool):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Validate required config
        self._validate_config()
        
        # Set defaults
        self.timeout = config.get('timeout', 30)
        self.retries = config.get('max_retries', 3)
    
    def _validate_config(self):
        required = ['api_key', 'endpoint']
        missing = [k for k in required if k not in self.config]
        if missing:
            raise ValueError(f"Missing config: {', '.join(missing)}")
3. Logging
pythonimport logging

logger = logging.getLogger(__name__)

class MyTool(BaseTool):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing {self.name} with input: {input_data.keys()}")
        
        try:
            result = self._process(input_data)
            logger.info(f"Execution successful")
            return result
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}", exc_info=True)
            raise
4. Input Validation
pythonfrom pydantic import BaseModel, validator

class EmailInput(BaseModel):
    to: str
    subject: str
    body: str
    
    @validator('to')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email address')
        return v

class EmailSenderTool(BaseTool):
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        try:
            EmailInput(**input_data)
            return True
        except Exception:
            return False
Advanced Features
Async Support
pythonimport asyncio
from typing import Dict, Any

class AsyncTool(BaseTool):
    async def execute_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous execution method.
        """
        await asyncio.sleep(1)  # Simulate async operation
        return {'success': True}
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper.
        """
        return asyncio.run(self.execute_async(input_data))
Streaming Results
pythonfrom typing import Iterator

class StreamingTool(BaseTool):
    def execute_stream(self, input_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Stream results as they become available.
        """
        for i in range(10):
            yield {'chunk': i, 'data': f'Item {i}'}
            time.sleep(0.1)
Caching
pythonfrom functools import lru_cache
import hashlib
import json

class CachedTool(BaseTool):
    @lru_cache(maxsize=100)
    def execute(self, input_hash: str) -> Dict[str, Any]:
        """
        Cached execution.
        """
        # Actual execution logic
        return self._execute_uncached(json.loads(input_hash))
    
    def _execute_uncached(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Real processing
        pass
    
    def execute_with_cache(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        input_hash = hashlib.md5(
            json.dumps(input_data, sort_keys=True).encode()
        ).hexdigest()
        return self.execute(input_hash)
Testing Tools
Unit Tests
pythonimport pytest
from unittest.mock import Mock, patch

def test_tool_execution(tool):
    """Test successful execution."""
    input_data = {'param': 'value'}
    result = tool.execute(input_data)
    assert result['success'] is True

def test_tool_validation(tool):
    """Test input validation."""
    assert tool.validate_input({'required': 'value'}) is True
    assert tool.validate_input({}) is False

def test_tool_error_handling(tool):
    """Test error handling."""
    with patch.object(tool, '_process', side_effect=Exception('Test error')):
        result = tool.execute({'param': 'value'})
        assert result['success'] is False
        assert 'error' in result
Integration Tests
python@pytest.mark.integration
def test_tool_integration():
    """Test tool with real dependencies."""
    config = load_test_config()
    tool = MyTool(config)
    
    input_data = create_test_input()
    result = tool.execute(input_data)
    
    assert result['success'] is True
    verify_side_effects()
Deployment
1. Version Control
tool_name/
├── CHANGELOG.md          # Version history
├── VERSION              # Current version
└── migrations/          # Schema migrations
2. Documentation
markdown# Tool Name

## Description
Brief description of what the tool does.

## Installation
\`\`\`bash
pip install tool-requirements
\`\`\`

## Configuration
Required and optional configuration parameters.

## Usage
\`\`\`python
tool = ToolName(config)
result = tool.execute(input_data)
\`\`\`

## Examples
Real-world usage examples.

## API Reference
Detailed API documentation.
3. Monitoring
pythonfrom prometheus_client import Counter, Histogram

execution_counter = Counter(
    'tool_executions_total',
    'Total tool executions',
    ['tool_name', 'status']
)

execution_duration = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration',
    ['tool_name']
)

class MonitoredTool(BaseTool):
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        with execution_duration.labels(tool_name=self.name).time():
            result = super().execute(input_data)
            status = 'success' if result['success'] else 'error'
            execution_counter.labels(
                tool_name=self.name,
                status=status
            ).inc()
            return result
Tool Marketplace
Publishing Tools

Create tool package
Write comprehensive documentation
Add example usage
Submit for review
Publish to registry

Using Third-party Tools
pythonfrom tools.registry import install_tool, load_tool

# Install from registry
install_tool('community/amazing-tool')

# Load and use
tool = load_tool('amazing-tool', config)
result = tool.execute(input_data)