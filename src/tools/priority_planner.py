"""
Priority planning and scheduling tool.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseTool

logger = logging.getLogger(__name__)


class PriorityPlannerTool(BaseTool):
    """
    Tool for creating prioritized daily plans.
    Uses intelligent scoring to rank tasks.
    """
    
    def __init__(self):
        super().__init__(
            name="create_priority_plan",
            description="Create prioritized daily plans with time blocking"
        )
        self.cache_ttl = 0  # Don't cache plans (always fresh)
    
    def _execute(
        self,
        tasks: List[Dict[str, Any]],
        calendar_events: List[Dict[str, Any]],
        free_blocks: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a priority plan.
        
        Args:
            tasks: List of tasks to prioritize
            calendar_events: Today's calendar events
            free_blocks: Available time blocks
            user_preferences: User preferences for planning
            
        Returns:
            Prioritized daily plan
        """
        logger.info(f"Creating priority plan for {len(tasks)} tasks")

        # VALIDATION: Ensure we have data
        if not tasks:
            logger.warning("No tasks provided to priority planner!")
            logger.debug(f"Tasks type: {type(tasks)}, value: {tasks}")
        
        if not calendar_events:
            logger.warning("No calendar events provided!")
        
        if not free_blocks:
            logger.warning("No free blocks provided!")
        
        # Score and rank tasks
        scored_tasks = self._score_tasks(tasks)
        
        # Allocate tasks to time blocks
        schedule = self._allocate_time_blocks(scored_tasks, free_blocks, user_preferences)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(scored_tasks, calendar_events, schedule)
        
        return {
            'success': True,
            'prioritized_tasks': scored_tasks[:10],  # Top 10
            'schedule': schedule,
            'suggestions': suggestions,
            'summary': {
                'total_tasks': len(tasks),
                'high_priority_count': sum(1 for t in scored_tasks if t['priority_score'] >= 80),
                'scheduled_tasks': len(schedule),
                'total_meeting_time': sum(e['duration_minutes'] for e in calendar_events),
                'total_free_time': sum(b['duration_minutes'] for b in free_blocks)
            }
        }
    
    def _score_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Score tasks using priority model.
        Score = (Urgency × 0.4) + (Impact × 0.3) + (Deadline × 0.2) + (Context × 0.1)
        """
        scored_tasks = []
        today = datetime.now().date()
        
        for task in tasks:
            # Calculate urgency (based on priority tag)
            urgency = self._calculate_urgency(task)
            
            # Calculate impact (based on project status, labels)
            impact = self._calculate_impact(task)
            
            # Calculate deadline proximity
            deadline_score = self._calculate_deadline_score(task, today)
            
            # Calculate context score (blockers, dependencies)
            context = self._calculate_context(task)
            
            # Final priority score
            priority_score = (
                urgency * 0.40 +
                impact * 0.30 +
                deadline_score * 0.20 +
                context * 0.10
            )
            
            task_with_score = task.copy()
            task_with_score['priority_score'] = round(priority_score, 1)
            task_with_score['urgency'] = urgency
            task_with_score['impact'] = impact
            task_with_score['deadline_score'] = deadline_score
            
            scored_tasks.append(task_with_score)
        
        # Sort by priority score (descending)
        scored_tasks.sort(key=lambda t: t['priority_score'], reverse=True)
        
        return scored_tasks
    
    def _calculate_urgency(self, task: Dict) -> float:
        """Calculate urgency score (0-100)."""
        priority_map = {
            'critical': 100,
            'high': 75,
            'medium': 50,
            'low': 25
        }
        
        base_score = priority_map.get(task.get('priority', 'medium'), 50)
        
        # Boost if blocked
        if task.get('blocked'):
            base_score = min(100, base_score + 15)
        
        # Boost if critical-path
        if 'critical-path' in task.get('labels', []):
            base_score = min(100, base_score + 10)
        
        return float(base_score)
    
    def _calculate_impact(self, task: Dict) -> float:
        """Calculate impact score (0-100)."""
        score = 50.0  # Base
        
        # Project importance
        if task.get('project') == 'Phoenix':
            score += 20  # Main project
        
        # Story points (bigger = more impact)
        story_points = task.get('story_points', 0)
        if story_points >= 5:
            score += 15
        elif story_points >= 3:
            score += 10
        
        # Labels
        labels = task.get('labels', [])
        if 'blocker' in labels:
            score += 20
        if 'external-dependency' in labels:
            score += 10
        
        return min(100.0, score)
    
    def _calculate_deadline_score(self, task: Dict, today: datetime.date) -> float:
        """Calculate deadline proximity score (0-100)."""
        due_date_str = task.get('due_date')
        if not due_date_str:
            return 50.0  # No deadline = medium urgency
        
        try:
            due_date = datetime.fromisoformat(due_date_str).date()
            days_until_due = (due_date - today).days
            
            if days_until_due < 0:
                return 100.0  # Overdue
            elif days_until_due == 0:
                return 100.0  # Due today
            elif days_until_due == 1:
                return 90.0   # Due tomorrow
            elif days_until_due <= 3:
                return 75.0   # Due this week
            elif days_until_due <= 7:
                return 60.0   # Due next week
            else:
                return max(30.0, 100 - (days_until_due * 3))
        except (ValueError, TypeError):
            return 50.0
    
    def _calculate_context(self, task: Dict) -> float:
        """Calculate contextual score (0-100)."""
        score = 50.0
        
        # In progress tasks get boost (momentum)
        if task.get('status') == 'in_progress':
            score += 30
        
        # Blocked tasks need attention
        if task.get('blocked'):
            score += 20
        
        return min(100.0, score)
    
    def _allocate_time_blocks(
        self,
        tasks: List[Dict],
        free_blocks: List[Dict],
        preferences: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Allocate tasks to available time blocks."""
        schedule = []
        preferences = preferences or {}
        
        # Get morning preference (default: True)
        prefer_morning_focus = preferences.get('morning_focus', True)
        
        # Sort free blocks by duration (longest first for deep work)
        sorted_blocks = sorted(
            free_blocks,
            key=lambda b: b['duration_minutes'],
            reverse=True
        )
        
        allocated_tasks = set()
        
        for block in sorted_blocks:
            block_duration = block['duration_minutes']
            
            # Skip very small blocks
            if block_duration < 30:
                continue
            
            # Determine if this is morning block
            block_start = datetime.fromisoformat(block['start_time'])
            is_morning = block_start.hour < 12
            
            # Find best task for this block
            for task in tasks:
                if task['id'] in allocated_tasks:
                    continue
                
                task_duration = task.get('estimated_hours', 1.0) * 60  # Convert to minutes
                
                # Check if task fits in block
                if task_duration <= block_duration:
                    # Prefer high-priority tasks in morning if preference set
                    if prefer_morning_focus and is_morning and task['priority_score'] >= 80:
                        schedule.append({
                            'task_id': task['id'],
                            'task_title': task['title'],
                            'priority_score': task['priority_score'],
                            'start_time': block['start_time'],
                            'end_time': (
                                datetime.fromisoformat(block['start_time']) +
                                timedelta(minutes=task_duration)
                            ).isoformat(),
                            'duration_minutes': task_duration,
                            'block_type': 'deep_work' if block_duration >= 90 else 'focused_task'
                        })
                        allocated_tasks.add(task['id'])
                        break
                    elif not is_morning or not prefer_morning_focus:
                        schedule.append({
                            'task_id': task['id'],
                            'task_title': task['title'],
                            'priority_score': task['priority_score'],
                            'start_time': block['start_time'],
                            'end_time': (
                                datetime.fromisoformat(block['start_time']) +
                                timedelta(minutes=task_duration)
                            ).isoformat(),
                            'duration_minutes': task_duration,
                            'block_type': 'focused_task'
                        })
                        allocated_tasks.add(task['id'])
                        break
        
        return schedule
    
    def _generate_suggestions(
        self,
        tasks: List[Dict],
        events: List[Dict],
        schedule: List[Dict]
    ) -> List[str]:
        """Generate proactive suggestions."""
        suggestions = []
        
        # Check for critical blockers
        critical_blocked = [
            t for t in tasks 
            if t.get('blocked') and t.get('priority', '') == 'critical'
        ]
        if critical_blocked:
            suggestions.append(
                f"⚠️ CRITICAL: {len(critical_blocked)} blocked task(s) need immediate escalation"
            )
        
        # Check for tasks due today
        today = datetime.now().date().isoformat()
        due_today = [t for t in tasks if t.get('due_date') == today]
        if due_today:
            suggestions.append(
                f"🎯 {len(due_today)} task(s) due today - prioritize completion"
            )
        
        # Check meeting density
        total_meeting_time = sum(e['duration_minutes'] for e in events)
        if total_meeting_time > 180:  # More than 3 hours
            suggestions.append(
                f"📅 Heavy meeting day ({total_meeting_time // 60}h {total_meeting_time % 60}m) - "
                "consider rescheduling non-critical meetings for focus time"
            )
        
        # Check if high-priority tasks are scheduled
        high_pri_tasks = [t for t in tasks if t['priority_score'] >= 80]
        scheduled_ids = {s['task_id'] for s in schedule}
        unscheduled_high_pri = [t for t in high_pri_tasks if t['id'] not in scheduled_ids]
        
        if unscheduled_high_pri:
            suggestions.append(
                f"⏰ {len(unscheduled_high_pri)} high-priority task(s) not scheduled - "
                "may need to defer lower-priority work"
            )
        
        return suggestions