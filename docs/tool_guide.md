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