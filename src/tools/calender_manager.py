"""
Calendar management tool for retrieving events and availability.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseTool, retry_on_failure

logger = logging.getLogger(__name__)


class CalendarManagerTool(BaseTool):
    """
    Tool for managing calendar operations.
    For demo purposes, generates mock calendar data.
    Can be extended to integrate with Google Calendar or Outlook.
    """
    
    def __init__(self):
        super().__init__(
            name="manage_calendar",
            description="View calendar events, check availability, and manage scheduling"
        )
        self.cache_ttl = 1800  # 30 minutes for calendar data
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def _execute(
        self,
        action: str = "get_events",
        date: Optional[str] = None,
        time_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute calendar operations.
        
        Args:
            action: Calendar action ("get_events", "check_availability")
            date: Date to query (ISO format or "today")
            time_range: Optional time range with start/end
            
        Returns:
            Calendar data
        """
        logger.info(f"Executing calendar action: {action}")
        
        # Parse date
        if date == "today" or not date:
            target_date = datetime.now()
        else:
            try:
                target_date = datetime.fromisoformat(date)
            except ValueError:
                target_date = datetime.now()
        
        if action == "get_events":
            return self._get_events(target_date)
        elif action == "check_availability":
            return self._check_availability(target_date)
        else:
            return {
                'error': 'invalid_action',
                'message': f"Unknown action: {action}"
            }
    
    def _get_events(self, date: datetime) -> Dict[str, Any]:
        """Get calendar events for a specific date."""
        
        # Generate mock events for demonstration
        # In production, this would call Google Calendar API or similar
        events = self._generate_mock_events(date)
        
        # Calculate free time blocks
        free_blocks = self._calculate_free_blocks(events, date)
        
        return {
            'success': True,
            'date': date.strftime('%Y-%m-%d'),
            'events': events,
            'free_blocks': free_blocks,
            'total_meeting_minutes': sum(e['duration_minutes'] for e in events),
            'total_free_minutes': sum(b['duration_minutes'] for b in free_blocks),
            'metadata': {
                'event_count': len(events),
                'free_block_count': len(free_blocks)
            }
        }
    
    def _check_availability(self, date: datetime) -> Dict[str, Any]:
        """Check availability for a date."""
        events = self._generate_mock_events(date)
        free_blocks = self._calculate_free_blocks(events, date)
        
        return {
            'success': True,
            'date': date.strftime('%Y-%m-%d'),
            'is_available': len(free_blocks) > 0,
            'free_blocks': free_blocks,
            'busy_periods': [
                {
                    'start': e['start_time'],
                    'end': e['end_time'],
                    'title': e['title']
                }
                for e in events
            ]
        }
    
    def _generate_mock_events(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Generate mock calendar events.
        Replace with real API integration.
        """
        # Check if it's a weekday
        if date.weekday() >= 5:  # Weekend
            return []
        
        # Generate typical workday events
        events = [
            {
                'id': 'evt_001',
                'title': 'Daily Standup - Phoenix Team',
                'start_time': f"{date.strftime('%Y-%m-%d')}T09:00:00",
                'end_time': f"{date.strftime('%Y-%m-%d')}T09:15:00",
                'duration_minutes': 15,
                'type': 'meeting',
                'attendees': ['Sarah Chen', 'Michael Rodriguez', 'Team'],
                'status': 'confirmed'
            },
            {
                'id': 'evt_002',
                'title': 'Design Review - Payment Flow',
                'start_time': f"{date.strftime('%Y-%m-%d')}T14:00:00",
                'end_time': f"{date.strftime('%Y-%m-%d')}T15:00:00",
                'duration_minutes': 60,
                'type': 'meeting',
                'attendees': ['Sarah Chen', 'Jessica Wong', 'Alex Kumar'],
                'status': 'confirmed'
            },
            {
                'id': 'evt_003',
                'title': '1:1 with Sarah (Product Sync)',
                'start_time': f"{date.strftime('%Y-%m-%d')}T16:00:00",
                'end_time': f"{date.strftime('%Y-%m-%d')}T16:30:00",
                'duration_minutes': 30,
                'type': 'meeting',
                'attendees': ['Sarah Chen'],
                'status': 'confirmed'
            }
        ]
        
        return events
    
    def _calculate_free_blocks(
        self, 
        events: List[Dict], 
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate free time blocks between meetings."""
        
        # Define work hours (9 AM - 6 PM)
        work_start = date.replace(hour=9, minute=0, second=0)
        work_end = date.replace(hour=18, minute=0, second=0)
        
        # Sort events by start time
        sorted_events = sorted(
            events, 
            key=lambda e: datetime.fromisoformat(e['start_time'])
        )
        
        free_blocks = []
        current_time = work_start
        
        for event in sorted_events:
            event_start = datetime.fromisoformat(event['start_time'])
            event_end = datetime.fromisoformat(event['end_time'])
            
            # Check if there's a gap before this event
            if current_time < event_start:
                gap_minutes = int((event_start - current_time).total_seconds() / 60)
                if gap_minutes >= 15:  # Only blocks 15+ minutes
                    free_blocks.append({
                        'start_time': current_time.isoformat(),
                        'end_time': event_start.isoformat(),
                        'duration_minutes': gap_minutes
                    })
            
            current_time = max(current_time, event_end)
        
        # Check for time after last meeting
        if current_time < work_end:
            gap_minutes = int((work_end - current_time).total_seconds() / 60)
            if gap_minutes >= 15:
                free_blocks.append({
                    'start_time': current_time.isoformat(),
                    'end_time': work_end.isoformat(),
                    'duration_minutes': gap_minutes
                })
        
        return free_blocks