"""
Unit tests for Email Tool.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime


class TestEmailTool:
    """Test suite for Email Tool."""
    
    @pytest.fixture
    def email_tool(self):
        """Create an EmailTool instance for testing."""
        from app.tools.email_tool import EmailTool
        return EmailTool()
    
    @pytest.fixture
    def valid_email_params(self):
        """Valid email parameters."""
        return {
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email."
        }
    
    def test_email_tool_initialization(self, email_tool):
        """Test email tool initializes correctly."""
        assert email_tool is not None
        assert email_tool.name == "email_tool"
        assert hasattr(email_tool, 'send_email')
    
    @pytest.mark.asyncio
    async def test_send_simple_email(self, email_tool, valid_email_params):
        """Test sending a simple email."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(valid_email_params)
            
            assert result['status'] == 'success'
            assert 'message_id' in result
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, email_tool):
        """Test sending email with attachments."""
        params = {
            "to": "recipient@example.com",
            "subject": "Email with Attachment",
            "body": "Please find attached.",
            "attachments": ["document.pdf", "image.jpg"]
        }
        
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', create=True):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result['attachments_count'] == 2
    
    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, email_tool):
        """Test sending email to multiple recipients."""
        params = {
            "to": ["user1@example.com", "user2@example.com", "user3@example.com"],
            "subject": "Team Update",
            "body": "Important team announcement"
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result['recipients_count'] == 3
    
    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, email_tool):
        """Test sending email with CC and BCC."""
        params = {
            "to": "primary@example.com",
            "cc": ["cc1@example.com", "cc2@example.com"],
            "bcc": ["bcc@example.com"],
            "subject": "Test CC/BCC",
            "body": "Testing CC and BCC functionality"
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result['total_recipients'] == 4  # 1 to + 2 cc + 1 bcc
    
    @pytest.mark.asyncio
    async def test_send_html_email(self, email_tool):
        """Test sending HTML formatted email."""
        params = {
            "to": "recipient@example.com",
            "subject": "HTML Email",
            "body": "<h1>Hello</h1><p>This is HTML</p>",
            "html": True
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result['format'] == 'html'
    
    @pytest.mark.asyncio
    async def test_invalid_email_address(self, email_tool):
        """Test handling of invalid email address."""
        params = {
            "to": "invalid-email",
            "subject": "Test",
            "body": "Test"
        }
        
        result = await email_tool.execute(params)
        
        assert result['status'] == 'error'
        assert 'invalid email' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, email_tool):
        """Test handling of missing required fields."""
        params = {
            "subject": "Test"  # Missing 'to' and 'body'
        }
        
        result = await email_tool.execute(params)
        
        assert result['status'] == 'error'
        assert 'required' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_smtp_connection_failure(self, email_tool, valid_email_params):
        """Test handling of SMTP connection failure."""
        with patch('smtplib.SMTP', side_effect=Exception("Connection refused")):
            result = await email_tool.execute(valid_email_params)
            
            assert result['status'] == 'error'
            assert 'connection' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, email_tool, valid_email_params):
        """Test handling of authentication failure."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_server.login.side_effect = Exception("Authentication failed")
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(valid_email_params)
            
            assert result['status'] == 'error'
            assert 'authentication' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_attachment_not_found(self, email_tool):
        """Test handling of missing attachment file."""
        params = {
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Test",
            "attachments": ["nonexistent.pdf"]
        }
        
        with patch('os.path.exists', return_value=False):
            result = await email_tool.execute(params)
            
            assert result['status'] == 'error'
            assert 'attachment' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_attachment_size_limit(self, email_tool):
        """Test attachment size validation."""
        params = {
            "to": "recipient@example.com",
            "subject": "Large Attachment",
            "body": "Test",
            "attachments": ["huge_file.zip"]
        }
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=30 * 1024 * 1024):  # 30 MB
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'error'
            assert 'size' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_read_email(self, email_tool):
        """Test reading emails from inbox."""
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = MagicMock()
            mock_mail.search.return_value = ('OK', [b'1 2 3'])
            mock_mail.fetch.return_value = ('OK', [(b'1', b'Email content')])
            mock_imap.return_value.__enter__.return_value = mock_mail
            
            result = await email_tool.read_emails(limit=10)
            
            assert result['status'] == 'success'
            assert len(result['emails']) > 0
    
    @pytest.mark.asyncio
    async def test_search_emails(self, email_tool):
        """Test searching emails."""
        params = {
            "query": "important project",
            "folder": "INBOX",
            "limit": 5
        }
        
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = MagicMock()
            mock_mail.search.return_value = ('OK', [b'1 2'])
            mock_imap.return_value.__enter__.return_value = mock_mail
            
            result = await email_tool.search_emails(params)
            
            assert result['status'] == 'success'
            assert 'emails' in result
    
    @pytest.mark.asyncio
    async def test_delete_email(self, email_tool):
        """Test deleting an email."""
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_mail = MagicMock()
            mock_imap.return_value.__enter__.return_value = mock_mail
            
            result = await email_tool.delete_email(email_id="123")
            
            assert result['status'] == 'success'
            mock_mail.store.assert_called()
    
    @pytest.mark.asyncio
    async def test_reply_to_email(self, email_tool):
        """Test replying to an email."""
        params = {
            "original_email_id": "123",
            "body": "Thank you for your email.",
            "reply_all": False
        }
        
        with patch('smtplib.SMTP') as mock_smtp, \
             patch('imaplib.IMAP4_SSL') as mock_imap:
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            mock_mail = MagicMock()
            mock_mail.fetch.return_value = ('OK', [(b'1', b'From: sender@example.com')])
            mock_imap.return_value.__enter__.return_value = mock_mail
            
            result = await email_tool.reply_to_email(params)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_validate_email_format(self, email_tool):
        """Test email format validation."""
        valid_emails = [
            "user@example.com",
            "first.last@company.co.uk",
            "user+tag@domain.com"
        ]
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com"
        ]
        
        for email in valid_emails:
            assert email_tool.validate_email(email) is True
        
        for email in invalid_emails:
            assert email_tool.validate_email(email) is False
    
    @pytest.mark.asyncio
    async def test_draft_email(self, email_tool):
        """Test creating email draft."""
        params = {
            "to": "recipient@example.com",
            "subject": "Draft Email",
            "body": "This is a draft"
        }
        
        result = await email_tool.create_draft(params)
        
        assert result['status'] == 'success'
        assert 'draft_id' in result
    
    @pytest.mark.parametrize("priority,expected_header", [
        ("high", "1"),
        ("normal", "3"),
        ("low", "5")
    ])
    @pytest.mark.asyncio
    async def test_email_priority(self, email_tool, priority, expected_header):
        """Test setting email priority."""
        params = {
            "to": "recipient@example.com",
            "subject": "Priority Test",
            "body": "Test",
            "priority": priority
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result['priority'] == priority