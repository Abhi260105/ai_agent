"""
Mock tool implementations for testing
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import time
import json


class BaseMockTool:
    """Base class for mock tools"""
    
    def __init__(
        self,
        latency_ms: float = 100,
        failure_rate: float = 0.0
    ):
        """
        Initialize base mock tool
        
        Args:
            latency_ms: Simulated latency in milliseconds
            failure_rate: Probability of failure (0.0 to 1.0)
        """
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []
    
    def _simulate_latency(self):
        """Simulate network/processing latency"""
        time.sleep(self.latency_ms / 1000)
    
    def _check_failure(self):
        """Check if this call should fail"""
        if random.random() < self.failure_rate:
            raise Exception(f"{self.__class__.__name__} mock failure")
    
    def _track_call(self, method: str, args: Dict[str, Any], result: Any):
        """Track tool call for testing"""
        self.call_count += 1
        self.call_history.append({
            "method": method,
            "args": args,
            "result": result,
            "timestamp": time.time()
        })
    
    def reset_stats(self):
        """Reset call tracking"""
        self.call_count = 0
        self.call_history = []


class MockEmailTool(BaseMockTool):
    """Mock email tool for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.emails = self._generate_sample_emails()
    
    def fetch_recent(
        self,
        limit: int = 10,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent emails
        
        Args:
            limit: Maximum number of emails to fetch
            unread_only: Only return unread emails
            
        Returns:
            List of email dictionaries
        """
        self._simulate_latency()
        self._check_failure()
        
        emails = self.emails.copy()
        
        if unread_only:
            emails = [e for e in emails if not e.get("read", False)]
        
        result = emails[:limit]
        self._track_call("fetch_recent", {"limit": limit, "unread_only": unread_only}, result)
        
        return result
    
    def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search emails by query"""
        self._simulate_latency()
        self._check_failure()
        
        # Simple search: check if query in subject or body
        results = [
            email for email in self.emails
            if query.lower() in email["subject"].lower()
            or query.lower() in email["body"].lower()
        ]
        
        result = results[:limit]
        self._track_call("search", {"query": query, "limit": limit}, result)
        
        return result
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read"""
        self._simulate_latency()
        self._check_failure()
        
        for email in self.emails:
            if email["id"] == email_id:
                email["read"] = True
                self._track_call("mark_as_read", {"email_id": email_id}, True)
                return True
        
        return False
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """Send an email"""
        self._simulate_latency()
        self._check_failure()
        
        email = {
            "id": f"email_{len(self.emails) + 1}",
            "from": "user@example.com",
            "to": to,
            "subject": subject,
            "body": body,
            "sent": datetime.now().isoformat(),
            "read": True
        }
        
        self.emails.append(email)
        self._track_call("send_email", {"to": to, "subject": subject}, email)
        
        return email
    
    def _generate_sample_emails(self) -> List[Dict[str, Any]]:
        """Generate sample emails for testing"""
        templates = [
            {
                "from": "boss@company.com",
                "subject": "Q1 Planning Meeting",
                "body": "Please prepare your Q1 objectives for review.",
                "priority": "high",
                "read": False
            },
            {
                "from": "team@company.com",
                "subject": "Sprint Review Tomorrow",
                "body": "Don't forget our sprint review at 2 PM.",
                "priority": "medium",
                "read": False
            },
            {
                "from": "hr@company.com",
                "subject": "Benefits Enrollment Reminder",
                "body": "Benefits enrollment closes Friday.",
                "priority": "low",
                "read": True
            },
            {
                "from": "client@external.com",
                "subject": "Demo Feedback",
                "body": "Great demo yesterday! A few questions...",
                "priority": "high",
                "read": False
            },
            {
                "from": "newsletter@tech.com",
                "subject": "Weekly Tech Digest",
                "body": "Top stories from this week in tech...",
                "priority": "low",
                "read": True
            }
        ]
        
        emails = []
        for i, template in enumerate(templates):
            email = {
                "id": f"email_{i+1:03d}",
                "received": (datetime.now() - timedelta(hours=i)).isoformat(),
                **template
            }
            emails.append(email)
        
        return emails


class MockCalendarTool(BaseMockTool):
    """Mock calendar tool for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = self._generate_sample_events()
    
    def get_events(
        self,
        days: int = 7,
        start_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events
        
        Args:
            days: Number of days to fetch
            start_date: Start date (ISO format)
            
        Returns:
            List of event dictionaries
        """
        self._simulate_latency()
        self._check_failure()
        
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now()
        
        end = start + timedelta(days=days)
        
        # Filter events in date range
        result = [
            event for event in self.events
            if start <= datetime.fromisoformat(event["start"]) <= end
        ]
        
        self._track_call("get_events", {"days": days, "start_date": start_date}, result)
        
        return result
    
    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a calendar event"""
        self._simulate_latency()
        self._check_failure()
        
        event = {
            "id": f"event_{len(self.events) + 1:03d}",
            "title": title,
            "start": start,
            "end": end,
            "location": location or "TBD",
            "attendees": attendees or [],
            "status": "confirmed"
        }
        
        self.events.append(event)
        self._track_call("create_event", {"title": title, "start": start}, event)
        
        return event
    
    def get_free_busy(
        self,
        start: str,
        end: str
    ) -> List[Dict[str, str]]:
        """Get free/busy information"""
        self._simulate_latency()
        self._check_failure()
        
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        
        busy_slots = []
        for event in self.events:
            event_start = datetime.fromisoformat(event["start"])
            event_end = datetime.fromisoformat(event["end"])
            
            if start_dt <= event_start <= end_dt or start_dt <= event_end <= end_dt:
                busy_slots.append({
                    "start": event["start"],
                    "end": event["end"]
                })
        
        self._track_call("get_free_busy", {"start": start, "end": end}, busy_slots)
        
        return busy_slots
    
    def _generate_sample_events(self) -> List[Dict[str, Any]]:
        """Generate sample calendar events"""
        now = datetime.now()
        
        events = [
            {
                "id": "event_001",
                "title": "Team Standup",
                "start": (now + timedelta(hours=1)).isoformat(),
                "end": (now + timedelta(hours=1, minutes=30)).isoformat(),
                "location": "Conference Room A",
                "attendees": ["team@company.com"],
                "status": "confirmed"
            },
            {
                "id": "event_002",
                "title": "1:1 with Manager",
                "start": (now + timedelta(hours=5)).isoformat(),
                "end": (now + timedelta(hours=5, minutes=30)).isoformat(),
                "location": "Virtual",
                "attendees": ["boss@company.com"],
                "status": "confirmed"
            },
            {
                "id": "event_003",
                "title": "Client Demo",
                "start": (now + timedelta(days=1, hours=3)).isoformat(),
                "end": (now + timedelta(days=1, hours=4)).isoformat(),
                "location": "Zoom",
                "attendees": ["client@external.com"],
                "status": "tentative"
            }
        ]
        
        return events


class MockTaskTool(BaseMockTool):
    """Mock task management tool"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = self._generate_sample_tasks()
    
    def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks with optional filters"""
        self._simulate_latency()
        self._check_failure()
        
        tasks = self.tasks.copy()
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        
        if priority:
            tasks = [t for t in tasks if t["priority"] == priority]
        
        self._track_call("get_tasks", {"status": status, "priority": priority}, tasks)
        
        return tasks
    
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new task"""
        self._simulate_latency()
        self._check_failure()
        
        task = {
            "id": f"task_{len(self.tasks) + 1:03d}",
            "title": title,
            "description": description,
            "priority": priority,
            "status": "todo",
            "due_date": due_date,
            "created": datetime.now().isoformat()
        }
        
        self.tasks.append(task)
        self._track_call("create_task", {"title": title, "priority": priority}, task)
        
        return task
    
    def update_task(
        self,
        task_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a task"""
        self._simulate_latency()
        self._check_failure()
        
        for task in self.tasks:
            if task["id"] == task_id:
                task.update(updates)
                self._track_call("update_task", {"task_id": task_id, **updates}, task)
                return task
        
        raise ValueError(f"Task {task_id} not found")
    
    def _generate_sample_tasks(self) -> List[Dict[str, Any]]:
        """Generate sample tasks"""
        return [
            {
                "id": "task_001",
                "title": "Complete Q1 objectives",
                "description": "Write Q1 planning document",
                "priority": "high",
                "status": "in_progress",
                "due_date": (datetime.now() + timedelta(days=2)).isoformat()
            },
            {
                "id": "task_002",
                "title": "Review sprint deliverables",
                "description": "Check all sprint items",
                "priority": "medium",
                "status": "todo",
                "due_date": (datetime.now() + timedelta(days=1)).isoformat()
            }
        ]


class MockSearchTool(BaseMockTool):
    """Mock search tool"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = self._build_search_index()
    
    def search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search the mock index"""
        self._simulate_latency()
        self._check_failure()
        
        # Simple keyword matching
        results = []
        for doc in self.index:
            if query.lower() in doc["content"].lower():
                results.append(doc)
        
        result = results[:limit]
        self._track_call("search", {"query": query, "limit": limit}, result)
        
        return result
    
    def _build_search_index(self) -> List[Dict[str, Any]]:
        """Build a mock search index"""
        return [
            {
                "id": "doc_001",
                "title": "Q1 Planning Guide",
                "content": "Guide for Q1 planning and objective setting",
                "type": "document"
            },
            {
                "id": "doc_002",
                "title": "Sprint Review Process",
                "content": "How to conduct effective sprint reviews",
                "type": "document"
            },
            {
                "id": "doc_003",
                "title": "Client Demo Best Practices",
                "content": "Tips for successful client demonstrations",
                "type": "guide"
            }
        ]
