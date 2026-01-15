"""
Notification Service - Handle various notification channels
"""

import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""
    
    @abstractmethod
    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """Send notification through this channel."""
        pass


class EmailNotification(NotificationChannel):
    """Email notification handler."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        """
        Initialize email notification.
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(self, recipient: str, subject: str, message: str, html: bool = False) -> bool:
        """
        Send email notification.
        
        Args:
            recipient: Email recipient
            subject: Email subject
            message: Email message
            html: Whether message is HTML
            
        Returns:
            Success status
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = subject
            
            if html:
                msg.attach(MIMEText(message, 'html'))
            else:
                msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


class WebhookNotification(NotificationChannel):
    """Webhook notification handler."""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict] = None):
        """
        Initialize webhook notification.
        
        Args:
            webhook_url: Webhook URL
            headers: Optional HTTP headers
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """
        Send webhook notification.
        
        Args:
            recipient: Not used for webhooks
            subject: Notification title
            message: Notification message
            **kwargs: Additional webhook payload data
            
        Returns:
            Success status
        """
        try:
            payload = {
                'title': subject,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                **kwargs
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Webhook sent successfully to {self.webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook: {str(e)}")
            return False


class SlackNotification(NotificationChannel):
    """Slack notification handler."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notification.
        
        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
    
    async def send(self, recipient: str, subject: str, message: str, **kwargs) -> bool:
        """
        Send Slack notification.
        
        Args:
            recipient: Slack channel (can be included in webhook)
            subject: Message title
            message: Message content
            **kwargs: Additional Slack message options
            
        Returns:
            Success status
        """
        try:
            payload = {
                'text': f"*{subject}*\n{message}",
                'blocks': [
                    {
                        'type': 'header',
                        'text': {
                            'type': 'plain_text',
                            'text': subject
                        }
                    },
                    {
                        'type': 'section',
                        'text': {
                            'type': 'mrkdwn',
                            'text': message
                        }
                    }
                ],
                **kwargs
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Slack notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False


class NotificationService:
    """Central notification service managing multiple channels."""
    
    def __init__(self):
        """Initialize notification service."""
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_history: List[Dict] = []
    
    def register_channel(self, name: str, channel: NotificationChannel):
        """
        Register a notification channel.
        
        Args:
            name: Channel name
            channel: NotificationChannel instance
        """
        self.channels[name] = channel
        logger.info(f"Registered notification channel: {name}")
    
    async def send_notification(
        self,
        channels: List[str],
        recipient: str,
        subject: str,
        message: str,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send notification through multiple channels.
        
        Args:
            channels: List of channel names to use
            recipient: Notification recipient
            subject: Notification subject
            message: Notification message
            **kwargs: Additional channel-specific options
            
        Returns:
            Dictionary of channel names to success status
        """
        results = {}
        
        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Channel not found: {channel_name}")
                results[channel_name] = False
                continue
            
            channel = self.channels[channel_name]
            success = await channel.send(recipient, subject, message, **kwargs)
            results[channel_name] = success
        
        # Record notification
        self.notification_history.append({
            'timestamp': datetime.now().isoformat(),
            'channels': channels,
            'recipient': recipient,
            'subject': subject,
            'results': results
        })
        
        return results
    
    async def notify_task_completed(
        self,
        task_id: str,
        task_description: str,
        result: str,
        recipient: str
    ):
        """
        Send task completion notification.
        
        Args:
            task_id: Task identifier
            task_description: Task description
            result: Task result
            recipient: Notification recipient
        """
        subject = f"Task Completed: {task_id}"
        message = f"""
Task: {task_description}
ID: {task_id}
Status: Completed
Result: {result}

Timestamp: {datetime.now().isoformat()}
        """.strip()
        
        await self.send_notification(
            channels=list(self.channels.keys()),
            recipient=recipient,
            subject=subject,
            message=message
        )
    
    async def notify_task_failed(
        self,
        task_id: str,
        task_description: str,
        error: str,
        recipient: str
    ):
        """
        Send task failure notification.
        
        Args:
            task_id: Task identifier
            task_description: Task description
            error: Error message
            recipient: Notification recipient
        """
        subject = f"Task Failed: {task_id}"
        message = f"""
Task: {task_description}
ID: {task_id}
Status: Failed
Error: {error}

Timestamp: {datetime.now().isoformat()}
        """.strip()
        
        await self.send_notification(
            channels=list(self.channels.keys()),
            recipient=recipient,
            subject=subject,
            message=message
        )
    
    def get_notification_history(self, limit: int = 100) -> List[Dict]:
        """
        Get notification history.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of notification records
        """
        return self.notification_history[-limit:]
    
    def clear_history(self):
        """Clear notification history."""
        self.notification_history = []
        logger.info("Notification history cleared")


# Global notification service instance
notification_service = NotificationService()