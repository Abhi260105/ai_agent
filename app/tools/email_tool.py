"""
Email Tool - Gmail API Integration
Provides email reading, searching, and sending capabilities
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import base64
import re

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.config import config
from app.utils.logger import get_logger

logger = get_logger("tools.email")


class EmailTool(BaseTool):
    """
    Email operations using Gmail API
    
    Supported actions:
    - fetch: Get recent emails
    - search: Search emails by criteria
    - read: Read specific email
    - send: Send new email
    - draft: Create draft
    """
    
    def __init__(self, mock_mode: bool = None):
        super().__init__(
            name="email_tool",
            description="Read, search, and send emails via Gmail"
        )
        
        # Use mock mode from config or parameter
        self.mock_mode = (
            mock_mode if mock_mode is not None
            else config.dev.enable_mock_tools
        )
        
        if not self.mock_mode:
            self._initialize_gmail_api()
        else:
            self.logger.info("Email tool running in MOCK MODE")
            self.service = None
    
    def _initialize_gmail_api(self):
        """
        Initialize Gmail API service
        Requires OAuth2 credentials
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import os
            import pickle
            
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.compose'
            ]
            
            creds = None
            token_path = 'data/gmail_token.pickle'
            creds_path = config.tools.google_credentials_path
            
            # Load existing credentials
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(creds_path):
                        self.logger.warning(
                            f"Gmail credentials not found at {creds_path}"
                        )
                        self.mock_mode = True
                        self.service = None
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        creds_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API initialized successfully")
            
        except ImportError:
            self.logger.error("Google API libraries not installed")
            self.mock_mode = True
            self.service = None
        except Exception as e:
            self.logger.error(f"Gmail API initialization failed: {e}")
            self.mock_mode = True
            self.service = None
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute email action"""
        action = tool_input.action.lower()
        params = tool_input.params
        
        if action == "fetch":
            return self._fetch_emails(params)
        elif action == "search":
            return self._search_emails(params)
        elif action == "read":
            return self._read_email(params)
        elif action == "send":
            return self._send_email(params)
        elif action == "draft":
            return self._create_draft(params)
        else:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
    
    def _fetch_emails(self, params: Dict[str, Any]) -> ToolResult:
        """
        Fetch recent emails
        
        Params:
            days: Number of days to fetch (default: 7)
            max_results: Maximum emails to fetch (default: 10)
            filter: Filter type (unread/all) (default: all)
        """
        days = params.get("days", 7)
        max_results = params.get("max_results", 10)
        filter_type = params.get("filter", "all")
        
        if self.mock_mode:
            return self._mock_fetch_emails(days, max_results, filter_type)
        
        try:
            # Build query
            query_parts = []
            
            # Date filter
            after_date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
            query_parts.append(f"after:{after_date}")
            
            # Unread filter
            if filter_type == "unread":
                query_parts.append("is:unread")
            
            query = " ".join(query_parts)
            
            # Fetch messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get message details
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            unread_count = sum(1 for e in emails if e.get('unread', False))
            
            return ToolResult(
                success=True,
                data={
                    "emails": emails,
                    "count": len(emails),
                    "unread_count": unread_count,
                    "days": days,
                    "filter": filter_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Fetch emails failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _search_emails(self, params: Dict[str, Any]) -> ToolResult:
        """
        Search emails by criteria
        
        Params:
            query: Search query
            max_results: Maximum results (default: 10)
        """
        query = params.get("query", "")
        max_results = params.get("max_results", 10)
        
        if not query:
            return ToolResult(
                success=False,
                error="Search query required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_search_emails(query, max_results)
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                email_data = self._get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return ToolResult(
                success=True,
                data={
                    "emails": emails,
                    "count": len(emails),
                    "query": query
                }
            )
            
        except Exception as e:
            self.logger.error(f"Search emails failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _read_email(self, params: Dict[str, Any]) -> ToolResult:
        """
        Read specific email
        
        Params:
            email_id: Email ID to read
        """
        email_id = params.get("email_id")
        
        if not email_id:
            return ToolResult(
                success=False,
                error="email_id required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_read_email(email_id)
        
        try:
            email_data = self._get_email_details(email_id)
            
            if not email_data:
                return ToolResult(
                    success=False,
                    error=f"Email {email_id} not found",
                    error_type="resource_not_found"
                )
            
            return ToolResult(
                success=True,
                data=email_data
            )
            
        except Exception as e:
            self.logger.error(f"Read email failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _send_email(self, params: Dict[str, Any]) -> ToolResult:
        """
        Send email
        
        Params:
            to: Recipient email
            subject: Email subject
            body: Email body
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
        """
        to = params.get("to")
        subject = params.get("subject", "")
        body = params.get("body", "")
        
        if not to:
            return ToolResult(
                success=False,
                error="Recipient (to) required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_send_email(to, subject, body)
        
        try:
            from email.mime.text import MIMEText
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if params.get('cc'):
                message['cc'] = params['cc']
            if params.get('bcc'):
                message['bcc'] = params['bcc']
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return ToolResult(
                success=True,
                data={
                    "message_id": sent_message['id'],
                    "to": to,
                    "subject": subject,
                    "sent": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Send email failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _create_draft(self, params: Dict[str, Any]) -> ToolResult:
        """Create email draft"""
        # Similar to send but creates draft
        # Implementation omitted for brevity
        return ToolResult(
            success=False,
            error="Draft creation not yet implemented",
            error_type="internal_error"
        )
    
    def _get_email_details(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed email information"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Check if unread
            unread = 'UNREAD' in message.get('labelIds', [])
            
            return {
                "id": email_id,
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body[:500],  # First 500 chars
                "body_full": body,
                "unread": unread,
                "labels": message.get('labelIds', [])
            }
            
        except Exception as e:
            self.logger.error(f"Get email details failed: {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    return base64.urlsafe_b64decode(data).decode()
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode()
        return ""
    
    # Mock implementations
    def _mock_fetch_emails(self, days, max_results, filter_type):
        """Mock fetch for testing"""
        emails = [
            {
                "id": f"mock_{i}",
                "subject": f"Test Email {i}",
                "from": f"sender{i}@example.com",
                "date": datetime.now().isoformat(),
                "body": f"This is test email {i}",
                "unread": i % 2 == 0
            }
            for i in range(1, min(max_results + 1, 6))
        ]
        
        if filter_type == "unread":
            emails = [e for e in emails if e["unread"]]
        
        return ToolResult(
            success=True,
            data={
                "emails": emails,
                "count": len(emails),
                "unread_count": sum(1 for e in emails if e["unread"]),
                "days": days,
                "filter": filter_type,
                "mock": True
            }
        )
    
    def _mock_search_emails(self, query, max_results):
        """Mock search for testing"""
        return ToolResult(
            success=True,
            data={
                "emails": [
                    {
                        "id": "mock_search_1",
                        "subject": f"Search result for: {query}",
                        "from": "sender@example.com",
                        "date": datetime.now().isoformat(),
                        "body": f"Email matching query: {query}"
                    }
                ],
                "count": 1,
                "query": query,
                "mock": True
            }
        )
    
    def _mock_read_email(self, email_id):
        """Mock read for testing"""
        return ToolResult(
            success=True,
            data={
                "id": email_id,
                "subject": "Mock Email",
                "from": "sender@example.com",
                "date": datetime.now().isoformat(),
                "body": "This is a mock email body.",
                "mock": True
            }
        )
    
    def _mock_send_email(self, to, subject, body):
        """Mock send for testing"""
        return ToolResult(
            success=True,
            data={
                "message_id": "mock_sent_123",
                "to": to,
                "subject": subject,
                "sent": True,
                "mock": True
            }
        )
    
    def get_capability(self) -> ToolCapability:
        """Get email tool capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=["fetch", "search", "read", "send", "draft"],
            required_params={
                "fetch": "",
                "search": "query",
                "read": "email_id",
                "send": "to, subject, body"
            },
            optional_params={
                "fetch": "days, max_results, filter",
                "search": "max_results",
                "send": "cc, bcc"
            },
            requires_auth=True,
            rate_limit=100,
            examples=[
                {
                    "action": "fetch",
                    "params": {"days": 7, "filter": "unread"},
                    "description": "Fetch unread emails from last 7 days"
                },
                {
                    "action": "send",
                    "params": {
                        "to": "team@example.com",
                        "subject": "Meeting Update",
                        "body": "The meeting has been rescheduled."
                    },
                    "description": "Send email to team"
                }
            ]
        )
    
    def health_check(self) -> bool:
        """Check Gmail API connectivity"""
        if self.mock_mode:
            return True
        
        try:
            # Try to get profile
            self.service.users().getProfile(userId='me').execute()
            return True
        except:
            return False


if __name__ == "__main__":
    """Test email tool"""
    print("📧 Testing Email Tool...")
    
    # Create email tool in mock mode
    email_tool = EmailTool(mock_mode=True)
    
    # Test fetch
    print("\n📥 Testing fetch...")
    result = email_tool.run(ToolInput(
        action="fetch",
        params={"days": 7, "filter": "unread"}
    ))
    print(f"   Success: {result.success}")
    print(f"   Emails: {result.data.get('count', 0)}")
    
    # Test send
    print("\n📤 Testing send...")
    result = email_tool.run(ToolInput(
        action="send",
        params={
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test email"
        }
    ))
    print(f"   Success: {result.success}")
    print(f"   Sent: {result.data.get('sent', False)}")
    
    print("\n✅ Email tool test complete")