"""
Calendar Tool - Google Calendar API Integration
Provides calendar event management and scheduling capabilities
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from app.tools.base_tool import BaseTool
from app.schemas.tool_schema import ToolInput, ToolResult, ToolCapability
from app.config import config
from app.utils.logger import get_logger

logger = get_logger("tools.calendar")


class CalendarTool(BaseTool):
    """
    Calendar operations using Google Calendar API
    
    Supported actions:
    - list_events: Get events in date range
    - create_event: Create new event
    - update_event: Update existing event
    - delete_event: Delete event
    - check_conflicts: Check for scheduling conflicts
    - find_availability: Find free time slots
    """
    
    def __init__(self, mock_mode: bool = None):
        super().__init__(
            name="calendar_tool",
            description="Manage Google Calendar events and scheduling"
        )
        
        self.mock_mode = (
            mock_mode if mock_mode is not None
            else config.dev.enable_mock_tools
        )
        
        if not self.mock_mode:
            self._initialize_calendar_api()
        else:
            self.logger.info("Calendar tool running in MOCK MODE")
            self.service = None
    
    def _initialize_calendar_api(self):
        """Initialize Google Calendar API service"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import os
            import pickle
            
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            creds = None
            token_path = 'data/calendar_token.pickle'
            creds_path = config.tools.google_credentials_path
            
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(creds_path):
                        self.logger.warning(
                            f"Calendar credentials not found at {creds_path}"
                        )
                        self.mock_mode = True
                        self.service = None
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        creds_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Calendar API initialized successfully")
            
        except ImportError:
            self.logger.error("Google API libraries not installed")
            self.mock_mode = True
            self.service = None
        except Exception as e:
            self.logger.error(f"Calendar API initialization failed: {e}")
            self.mock_mode = True
            self.service = None
    
    def execute(self, tool_input: ToolInput) -> ToolResult:
        """Execute calendar action"""
        action = tool_input.action.lower()
        params = tool_input.params
        
        action_map = {
            "list_events": self._list_events,
            "create_event": self._create_event,
            "update_event": self._update_event,
            "delete_event": self._delete_event,
            "check_conflicts": self._check_conflicts,
            "find_availability": self._find_availability
        }
        
        handler = action_map.get(action)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}",
                error_type="validation"
            )
        
        return handler(params)
    
    def _list_events(self, params: Dict[str, Any]) -> ToolResult:
        """
        List calendar events
        
        Params:
            start_date: Start date (ISO format or relative like 'today')
            end_date: End date (ISO format or relative like 'next_week')
            max_results: Maximum events to return (default: 10)
        """
        start_date = params.get("start_date", "today")
        end_date = params.get("end_date", "next_week")
        max_results = params.get("max_results", 10)
        
        # Parse relative dates
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)
        
        if self.mock_mode:
            return self._mock_list_events(start_dt, end_dt, max_results)
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_dt.isoformat() + 'Z',
                timeMax=end_dt.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = [
                self._format_event(event) for event in events
            ]
            
            return ToolResult(
                success=True,
                data={
                    "events": formatted_events,
                    "count": len(formatted_events),
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"List events failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _create_event(self, params: Dict[str, Any]) -> ToolResult:
        """
        Create calendar event
        
        Params:
            title: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            attendees: List of attendee emails (optional)
            description: Event description (optional)
            location: Event location (optional)
        """
        title = params.get("title")
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        
        if not all([title, start_time, end_time]):
            return ToolResult(
                success=False,
                error="title, start_time, and end_time are required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_create_event(title, start_time, end_time, params)
        
        try:
            # Check for conflicts first
            conflicts = self._find_conflicts(start_time, end_time)
            if conflicts:
                return ToolResult(
                    success=False,
                    error="Time slot conflicts with existing event",
                    error_type="conflict",
                    data={
                        "conflicts": conflicts,
                        "suggested_times": self._suggest_alternative_times(
                            start_time, end_time
                        )
                    }
                )
            
            # Build event
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                }
            }
            
            if params.get('description'):
                event['description'] = params['description']
            
            if params.get('location'):
                event['location'] = params['location']
            
            if params.get('attendees'):
                event['attendees'] = [
                    {'email': email}
                    for email in params['attendees']
                ]
            
            # Create event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return ToolResult(
                success=True,
                data={
                    "event_id": created_event['id'],
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "created": True,
                    "link": created_event.get('htmlLink')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Create event failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _update_event(self, params: Dict[str, Any]) -> ToolResult:
        """Update existing event"""
        event_id = params.get("event_id")
        
        if not event_id:
            return ToolResult(
                success=False,
                error="event_id required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_update_event(event_id, params)
        
        # Implementation omitted for brevity
        return ToolResult(
            success=False,
            error="Update not yet implemented",
            error_type="internal_error"
        )
    
    def _delete_event(self, params: Dict[str, Any]) -> ToolResult:
        """Delete event"""
        event_id = params.get("event_id")
        
        if not event_id:
            return ToolResult(
                success=False,
                error="event_id required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_delete_event(event_id)
        
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return ToolResult(
                success=True,
                data={
                    "event_id": event_id,
                    "deleted": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Delete event failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                error_type="external_api"
            )
    
    def _check_conflicts(self, params: Dict[str, Any]) -> ToolResult:
        """
        Check for scheduling conflicts
        
        Params:
            start_time: Proposed start time
            end_time: Proposed end time
        """
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        
        if not all([start_time, end_time]):
            return ToolResult(
                success=False,
                error="start_time and end_time required",
                error_type="validation"
            )
        
        if self.mock_mode:
            return self._mock_check_conflicts(start_time, end_time)
        
        conflicts = self._find_conflicts(start_time, end_time)
        
        return ToolResult(
            success=True,
            data={
                "has_conflicts": len(conflicts) > 0,
                "conflicts": conflicts,
                "conflict_count": len(conflicts)
            }
        )
    
    def _find_availability(self, params: Dict[str, Any]) -> ToolResult:
        """Find available time slots"""
        # Implementation omitted for brevity
        return ToolResult(
            success=False,
            error="Find availability not yet implemented",
            error_type="internal_error"
        )
    
    def _find_conflicts(self, start_time: str, end_time: str) -> List[Dict]:
        """Find conflicting events"""
        if self.mock_mode:
            return []
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            return [
                self._format_event(event)
                for event in events_result.get('items', [])
            ]
            
        except Exception as e:
            self.logger.error(f"Find conflicts failed: {e}")
            return []
    
    def _suggest_alternative_times(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict]:
        """Suggest alternative time slots"""
        # Simple implementation: suggest next hour and day after
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = end_dt - start_dt
        
        alternatives = []
        
        # Next hour
        next_hour = start_dt + timedelta(hours=1)
        alternatives.append({
            "start_time": next_hour.isoformat(),
            "end_time": (next_hour + duration).isoformat()
        })
        
        # Next day same time
        next_day = start_dt + timedelta(days=1)
        alternatives.append({
            "start_time": next_day.isoformat(),
            "end_time": (next_day + duration).isoformat()
        })
        
        return alternatives
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string (ISO or relative)"""
        date_str = date_str.lower()
        
        if date_str == "today":
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == "tomorrow":
            return (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_str == "next_week":
            return (datetime.now() + timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    
    def _format_event(self, event: Dict) -> Dict:
        """Format event for output"""
        return {
            "id": event.get('id'),
            "title": event.get('summary', 'No title'),
            "start_time": event['start'].get('dateTime', event['start'].get('date')),
            "end_time": event['end'].get('dateTime', event['end'].get('date')),
            "location": event.get('location'),
            "description": event.get('description'),
            "attendees": [
                a.get('email') for a in event.get('attendees', [])
            ]
        }
    
    # Mock implementations
    def _mock_list_events(self, start_dt, end_dt, max_results):
        """Mock list for testing"""
        events = [
            {
                "id": f"mock_event_{i}",
                "title": f"Meeting {i}",
                "start_time": (start_dt + timedelta(days=i)).isoformat(),
                "end_time": (start_dt + timedelta(days=i, hours=1)).isoformat(),
                "location": "Office"
            }
            for i in range(min(max_results, 3))
        ]
        
        return ToolResult(
            success=True,
            data={
                "events": events,
                "count": len(events),
                "mock": True
            }
        )
    
    def _mock_create_event(self, title, start_time, end_time, params):
        """Mock create for testing"""
        return ToolResult(
            success=True,
            data={
                "event_id": "mock_event_123",
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "created": True,
                "mock": True
            }
        )
    
    def _mock_update_event(self, event_id, params):
        """Mock update for testing"""
        return ToolResult(
            success=True,
            data={
                "event_id": event_id,
                "updated": True,
                "mock": True
            }
        )
    
    def _mock_delete_event(self, event_id):
        """Mock delete for testing"""
        return ToolResult(
            success=True,
            data={
                "event_id": event_id,
                "deleted": True,
                "mock": True
            }
        )
    
    def _mock_check_conflicts(self, start_time, end_time):
        """Mock conflict check"""
        return ToolResult(
            success=True,
            data={
                "has_conflicts": False,
                "conflicts": [],
                "conflict_count": 0,
                "mock": True
            }
        )
    
    def get_capability(self) -> ToolCapability:
        """Get calendar tool capability"""
        return ToolCapability(
            name=self.name,
            description=self.description,
            supported_actions=[
                "list_events",
                "create_event",
                "update_event",
                "delete_event",
                "check_conflicts",
                "find_availability"
            ],
            required_params={
                "list_events": "",
                "create_event": "title, start_time, end_time",
                "update_event": "event_id",
                "delete_event": "event_id",
                "check_conflicts": "start_time, end_time"
            },
            optional_params={
                "list_events": "start_date, end_date, max_results",
                "create_event": "attendees, description, location"
            },
            requires_auth=True,
            rate_limit=50,
            examples=[
                {
                    "action": "create_event",
                    "params": {
                        "title": "Team Meeting",
                        "start_time": "2024-03-15T10:00:00Z",
                        "end_time": "2024-03-15T11:00:00Z",
                        "attendees": ["team@example.com"]
                    },
                    "description": "Schedule team meeting"
                }
            ]
        )
    
    def health_check(self) -> bool:
        """Check Calendar API connectivity"""
        if self.mock_mode:
            return True
        
        try:
            self.service.calendarList().list().execute()
            return True
        except:
            return False


if __name__ == "__main__":
    """Test calendar tool"""
    print("📅 Testing Calendar Tool...")
    
    calendar_tool = CalendarTool(mock_mode=True)
    
    # Test list events
    print("\n📋 Testing list events...")
    result = calendar_tool.run(ToolInput(
        action="list_events",
        params={"start_date": "today", "end_date": "next_week"}
    ))
    print(f"   Success: {result.success}")
    print(f"   Events: {result.data.get('count', 0)}")
    
    # Test create event
    print("\n➕ Testing create event...")
    result = calendar_tool.run(ToolInput(
        action="create_event",
        params={
            "title": "Test Meeting",
            "start_time": "2024-03-15T10:00:00Z",
            "end_time": "2024-03-15T11:00:00Z"
        }
    ))
    print(f"   Success: {result.success}")
    print(f"   Created: {result.data.get('created', False)}")
    
    print("\n✅ Calendar tool test complete")