"""
Task management tool for querying and managing tasks.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from .base import BaseTool, retry_on_failure

logger = logging.getLogger(__name__)


class TaskManagerTool(BaseTool):
    """
    Tool for managing tasks and to-dos.
    Integrates with project management systems.
    """
    
    def __init__(self, jira_client=None):
        super().__init__(
            name="manage_tasks",
            description="Query, create, update, and manage tasks"
        )
        self.jira_client = jira_client
        self.cache_ttl = 300  # 5 minutes
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _execute(
        self,
        action: str = "query_tasks",
        user_email: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "due_date"
    ) -> Dict[str, Any]:
        """
        Execute task management operations.
        
        Args:
            action: Task action ("query_tasks", "get_my_tasks")
            user_email: User email for filtering
            filters: Additional filters
            sort_by: Sort field
            
        Returns:
            Task data
        """
        logger.info(f"Executing task action: {action}")
        
        if action == "query_tasks" or action == "get_my_tasks":
            return self._query_tasks(user_email, filters, sort_by)
        else:
            return {
                'error': 'invalid_action',
                'message': f"Unknown action: {action}"
            }
    
    def _query_tasks(
        self,
        user_email: Optional[str],
        filters: Optional[Dict],
        sort_by: str
    ) -> Dict[str, Any]:
        """Query tasks with filters."""
        
        # For demo, generate mock tasks
        # In production, query from Jira using self.jira_client
        tasks = self._generate_mock_tasks(user_email)
        
        # Apply filters
        if filters:
            tasks = self._apply_filters(tasks, filters)
        
        # Sort tasks
        tasks = self._sort_tasks(tasks, sort_by)
        
        return {
            'success': True,
            'tasks': tasks,
            'total_count': len(tasks),
            'metadata': {
                'filters_applied': filters or {},
                'sort_by': sort_by
            }
        }
    
    def _generate_mock_tasks(self, user_email: Optional[str]) -> List[Dict[str, Any]]:
        """Generate mock tasks for demonstration."""
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        thursday = today + timedelta(days=3)
        friday = today + timedelta(days=4)
        next_week = today + timedelta(days=7)
        
        tasks = [
            {
                'id': 'PHOE-178',
                'title': 'Review API spec for payment integration',
                'project': 'Phoenix',
                'status': 'todo',
                'priority': 'high',
                'due_date': today.isoformat(),
                'created_date': (today - timedelta(days=3)).isoformat(),
                'estimated_hours': 2.0,
                'story_points': 5,
                'labels': ['review', 'api', 'critical-path'],
                'assignee': user_email or 'john.doe@company.com',
                'description': 'Review the updated API spec from engineering and provide feedback'
            },
            {
                'id': 'PHOE-145',
                'title': 'Follow up on vendor API key delay',
                'project': 'Phoenix',
                'status': 'in_progress',
                'priority': 'critical',
                'due_date': tomorrow.isoformat(),
                'created_date': (today - timedelta(days=8)).isoformat(),
                'estimated_hours': 1.0,
                'story_points': 3,
                'labels': ['blocker', 'external-dependency'],
                'assignee': user_email or 'john.doe@company.com',
                'blocked': True,
                'blocker_reason': 'Waiting on vendor response'
            },
            {
                'id': 'PHOE-189',
                'title': 'Prepare sprint demo slides',
                'project': 'Phoenix',
                'status': 'todo',
                'priority': 'medium',
                'due_date': friday.isoformat(),
                'created_date': (today - timedelta(days=2)).isoformat(),
                'estimated_hours': 1.5,
                'story_points': 3,
                'labels': ['demo', 'presentation'],
                'assignee': user_email or 'john.doe@company.com'
            },
            {
                'id': 'ATLS-234',
                'title': 'Review Q1 roadmap with Atlas team',
                'project': 'Atlas',
                'status': 'todo',
                'priority': 'high',
                'due_date': thursday.isoformat(),
                'created_date': (today - timedelta(days=5)).isoformat(),
                'estimated_hours': 2.0,
                'story_points': 5,
                'labels': ['planning', 'roadmap'],
                'assignee': user_email or 'john.doe@company.com'
            },
            {
                'id': 'ATLS-245',
                'title': 'Approve design mockups for Atlas v2',
                'project': 'Atlas',
                'status': 'in_progress',
                'priority': 'medium',
                'due_date': next_week.isoformat(),
                'created_date': (today - timedelta(days=1)).isoformat(),
                'estimated_hours': 1.0,
                'story_points': 2,
                'labels': ['design', 'approval'],
                'assignee': user_email or 'john.doe@company.com'
            },
            {
                'id': 'PHOE-201',
                'title': 'Update user documentation for new payment flow',
                'project': 'Phoenix',
                'status': 'todo',
                'priority': 'low',
                'due_date': next_week.isoformat(),
                'created_date': today.isoformat(),
                'estimated_hours': 3.0,
                'story_points': 5,
                'labels': ['documentation'],
                'assignee': user_email or 'john.doe@company.com'
            }
        ]
        
        return tasks
    
    def _apply_filters(self, tasks: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to task list."""
        filtered = tasks
        
        if 'status' in filters:
            status_filter = filters['status']
            if isinstance(status_filter, str):
                filtered = [t for t in filtered if t['status'] == status_filter]
            elif isinstance(status_filter, list):
                filtered = [t for t in filtered if t['status'] in status_filter]
        
        if 'priority' in filters:
            filtered = [t for t in filtered if t['priority'] == filters['priority']]
        
        if 'project' in filters:
            filtered = [t for t in filtered if t['project'] == filters['project']]
        
        if 'due_before' in filters:
            due_date = datetime.fromisoformat(filters['due_before']).date()
            filtered = [
                t for t in filtered 
                if datetime.fromisoformat(t['due_date']).date() <= due_date
            ]
        
        return filtered
    
    def _sort_tasks(self, tasks: List[Dict], sort_by: str) -> List[Dict]:
        """Sort tasks by specified field."""
        
        if sort_by == 'due_date':
            return sorted(tasks, key=lambda t: t.get('due_date', '9999-12-31'))
        elif sort_by == 'priority':
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            return sorted(tasks, key=lambda t: priority_order.get(t.get('priority', 'low'), 99))
        elif sort_by == 'created_date':
            return sorted(tasks, key=lambda t: t.get('created_date', ''))
        else:
            return tasks