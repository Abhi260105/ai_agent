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