"""
Unit tests for Calendar Tool.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta


class TestCalendarTool:
    """Test suite for Calendar Tool."""
    
    @pytest.fixture
    def calendar_tool(self):
        """Create a CalendarTool instance for testing."""
        from app.tools.calendar_tool import CalendarTool
        return CalendarTool()
    
    @pytest.fixture
    def valid_event_params(self):
        """Valid event parameters."""
        return {
            "title": "Team Meeting",
            "start": "2025-01-10T10:00:00Z",
            "end": "2025-01-10T11:00:00Z",
            "attendees": ["alice@example.com", "bob@example.com"]
        }
    
    def test_calendar_tool_initialization(self, calendar_tool):
        """Test calendar tool initializes correctly."""
        assert calendar_tool is not None
        assert calendar_tool.name == "calendar_tool"
        assert hasattr(calendar_tool, 'create_event')
    
    @pytest.mark.asyncio
    async def test_create_simple_event(self, calendar_tool, valid_event_params):
        """Test creating a simple calendar event."""
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.execute(valid_event_params)
            
            assert result['status'] == 'success'
            assert 'event_id' in result
    
    @pytest.mark.asyncio
    async def test_create_recurring_event(self, calendar_tool):
        """Test creating a recurring event."""
        params = {
            "title": "Daily Standup",
            "start": "2025-01-10T09:00:00Z",
            "end": "2025-01-10T09:30:00Z",
            "recurrence": "RRULE:FREQ=DAILY;COUNT=10"
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'recurring_event_123',
                'status': 'confirmed',
                'recurrence': [params['recurrence']]
            }
            
            result = await calendar_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('is_recurring') is True
    
    @pytest.mark.asyncio
    async def test_check_availability(self, calendar_tool):
        """Test checking calendar availability."""
        params = {
            "start": "2025-01-10T10:00:00Z",
            "end": "2025-01-10T17:00:00Z",
            "attendees": ["alice@example.com"]
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.freebusy().query().execute.return_value = {
                'calendars': {
                    'alice@example.com': {
                        'busy': []
                    }
                }
            }
            
            result = await calendar_tool.check_availability(params)
            
            assert result['status'] == 'success'
            assert result['available'] is True
    
    @pytest.mark.asyncio
    async def test_find_available_slots(self, calendar_tool):
        """Test finding available meeting slots."""
        params = {
            "duration": 60,  # minutes
            "attendees": ["alice@example.com", "bob@example.com"],
            "date_range": {
                "start": "2025-01-10T09:00:00Z",
                "end": "2025-01-10T17:00:00Z"
            }
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.freebusy().query().execute.return_value = {
                'calendars': {
                    'alice@example.com': {'busy': []},
                    'bob@example.com': {'busy': []}
                }
            }
            
            result = await calendar_tool.find_available_slots(params)
            
            assert result['status'] == 'success'
            assert len(result['available_slots']) > 0
    
    @pytest.mark.asyncio
    async def test_list_events(self, calendar_tool):
        """Test listing calendar events."""
        params = {
            "start_date": "2025-01-10T00:00:00Z",
            "end_date": "2025-01-17T00:00:00Z"
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().list().execute.return_value = {
                'items': [
                    {
                        'id': 'event_1',
                        'summary': 'Meeting 1',
                        'start': {'dateTime': '2025-01-10T10:00:00Z'}
                    },
                    {
                        'id': 'event_2',
                        'summary': 'Meeting 2',
                        'start': {'dateTime': '2025-01-11T14:00:00Z'}
                    }
                ]
            }
            
            result = await calendar_tool.list_events(params)
            
            assert result['status'] == 'success'
            assert len(result['events']) == 2
    
    @pytest.mark.asyncio
    async def test_update_event(self, calendar_tool):
        """Test updating a calendar event."""
        params = {
            "event_id": "event_123",
            "title": "Updated Meeting Title",
            "start": "2025-01-10T11:00:00Z"
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().patch().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.update_event(params)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_delete_event(self, calendar_tool):
        """Test deleting a calendar event."""
        event_id = "event_123"
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().delete().execute.return_value = None
            
            result = await calendar_tool.delete_event(event_id)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_add_attendees(self, calendar_tool):
        """Test adding attendees to an event."""
        params = {
            "event_id": "event_123",
            "attendees": ["charlie@example.com", "david@example.com"]
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            # Mock getting current event
            mock_service.events().get().execute.return_value = {
                'id': 'event_123',
                'attendees': [{'email': 'alice@example.com'}]
            }
            
            # Mock updating event
            mock_service.events().patch().execute.return_value = {
                'id': 'event_123',
                'attendees': [
                    {'email': 'alice@example.com'},
                    {'email': 'charlie@example.com'},
                    {'email': 'david@example.com'}
                ]
            }
            
            result = await calendar_tool.add_attendees(params)
            
            assert result['status'] == 'success'
            assert result['attendees_count'] == 3
    
    @pytest.mark.asyncio
    async def test_send_meeting_invite(self, calendar_tool, valid_event_params):
        """Test sending meeting invitations."""
        valid_event_params['send_invites'] = True
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.execute(valid_event_params)
            
            assert result['status'] == 'success'
            assert result.get('invites_sent') is True
    
    @pytest.mark.asyncio
    async def test_schedule_conflict_detection(self, calendar_tool):
        """Test detecting scheduling conflicts."""
        params = {
            "title": "New Meeting",
            "start": "2025-01-10T10:00:00Z",
            "end": "2025-01-10T11:00:00Z",
            "attendees": ["alice@example.com"]
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            # Simulate existing conflicting event
            mock_service.freebusy().query().execute.return_value = {
                'calendars': {
                    'alice@example.com': {
                        'busy': [{
                            'start': '2025-01-10T10:30:00Z',
                            'end': '2025-01-10T11:30:00Z'
                        }]
                    }
                }
            }
            
            result = await calendar_tool.check_conflicts(params)
            
            assert result['has_conflicts'] is True
            assert len(result['conflicts']) > 0
    
    @pytest.mark.asyncio
    async def test_set_event_reminder(self, calendar_tool):
        """Test setting event reminders."""
        params = {
            "event_id": "event_123",
            "reminders": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 15}
            ]
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().patch().execute.return_value = {
                'id': 'event_123',
                'reminders': {
                    'useDefault': False,
                    'overrides': params['reminders']
                }
            }
            
            result = await calendar_tool.set_reminders(params)
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_get_event_details(self, calendar_tool):
        """Test retrieving event details."""
        event_id = "event_123"
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().get().execute.return_value = {
                'id': 'event_123',
                'summary': 'Team Meeting',
                'start': {'dateTime': '2025-01-10T10:00:00Z'},
                'end': {'dateTime': '2025-01-10T11:00:00Z'},
                'attendees': [
                    {'email': 'alice@example.com', 'responseStatus': 'accepted'},
                    {'email': 'bob@example.com', 'responseStatus': 'tentative'}
                ]
            }
            
            result = await calendar_tool.get_event(event_id)
            
            assert result['status'] == 'success'
            assert result['event']['summary'] == 'Team Meeting'
            assert len(result['event']['attendees']) == 2
    
    @pytest.mark.asyncio
    async def test_accept_meeting_invite(self, calendar_tool):
        """Test accepting a meeting invitation."""
        event_id = "event_123"
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().patch().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.respond_to_invite(event_id, response="accepted")
            
            assert result['status'] == 'success'
            assert result['response'] == 'accepted'
    
    @pytest.mark.asyncio
    async def test_invalid_date_range(self, calendar_tool):
        """Test handling of invalid date range."""
        params = {
            "title": "Meeting",
            "start": "2025-01-10T11:00:00Z",
            "end": "2025-01-10T10:00:00Z"  # End before start
        }
        
        result = await calendar_tool.execute(params)
        
        assert result['status'] == 'error'
        assert 'date' in result['error'].lower() or 'time' in result['error'].lower()
    
    @pytest.mark.asyncio
    async def test_timezone_handling(self, calendar_tool):
        """Test handling different timezones."""
        params = {
            "title": "International Meeting",
            "start": "2025-01-10T10:00:00",
            "end": "2025-01-10T11:00:00",
            "timezone": "America/New_York"
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('timezone') == "America/New_York"
    
    @pytest.mark.asyncio
    async def test_all_day_event(self, calendar_tool):
        """Test creating an all-day event."""
        params = {
            "title": "Company Holiday",
            "date": "2025-01-15",
            "all_day": True
        }
        
        with patch.object(calendar_tool, 'calendar_service') as mock_service:
            mock_service.events().insert().execute.return_value = {
                'id': 'event_123',
                'status': 'confirmed'
            }
            
            result = await calendar_tool.execute(params)
            
            assert result['status'] == 'success'
            assert result.get('all_day') is True
    
    @pytest.mark.parametrize("duration,expected_slots", [
        (30, 8),   # 30-min slots in 4 hours
        (60, 4),   # 60-min slots in 4 hours
        (120, 2),  # 120-min slots in 4 hours
    ])
    @pytest.mark.asyncio
    async def test_slot_calculation(self, calendar_tool, duration, expected_slots):
        """Test calculating available time slots."""
        params = {
            "duration": duration,
            "date_range": {
                "start": "2025-01-10T09:00:00Z",
                "end": "2025-01-10T13:00:00Z"  # 4 hours
            }
        }
        
        slots = calendar_tool.calculate_slots(params)
        assert len(slots) == expected_slots