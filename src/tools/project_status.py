"""
Project status retrieval tool.
Integrates with Jira to fetch project information.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .base import BaseTool, retry_on_failure
from ..integrations.jira_client import JiraClient

logger = logging.getLogger(__name__)


class ProjectStatusTool(BaseTool):
    """
    Tool for retrieving project status from Jira.
    """
    
    def __init__(self, jira_client: JiraClient):
        super().__init__(
            name="get_project_status",
            description="Retrieve current project status, metrics, tasks, and blockers from Jira"
        )
        self.jira_client = jira_client
        self.cache_ttl = 300  # 5 minutes for project status
    
    def _generate_demo_data(self, project_id: str) -> Dict[str, Any]:
        """Generate realistic demo data for projects not in Jira."""
        logger.info(f"Generating demo data for project: {project_id}")
        
        from datetime import datetime, timedelta
        
        # Create realistic demo data
        return {
            'success': True,
            'project_name': f"Project {project_id.title()}",
            'project_key': project_id.upper()[:3],
            'project_id': 'demo-' + project_id.lower(),
            'status': 'on_track',
            'completion_percentage': 67.5,
            'sprint_info': {
                'sprint_id': 'demo-sprint-1',
                'sprint_name': 'Sprint 23',
                'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'state': 'active',
                'completed_points': 18,
                'total_points': 25
            },
            'metrics': {
                'total_tasks': 24,
                'completed_tasks': 16,
                'in_progress_tasks': 5,
                'blocked_tasks': 1,
                'todo_tasks': 2,
                'completion_percentage': 67.5,
                'story_points': {
                    'total': 58,
                    'completed': 39,
                    'remaining': 19
                }
            },
            'blockers': [
                {
                    'task_id': 'DEMO-123',
                    'task_title': 'API Integration with Payment Gateway',
                    'severity': 'high',
                    'blocked_since': (datetime.now() - timedelta(days=3)).isoformat(),
                    'blocker_reason': 'Waiting on vendor API credentials',
                    'owner': 'Sarah Chen',
                    'status': 'Blocked'
                }
            ],
            'tasks': [
                {
                    'id': 'DEMO-120',
                    'title': 'Implement user authentication flow',
                    'status': 'Done',
                    'assignee': 'Alex Thompson',
                    'priority': 'High',
                    'story_points': 5
                },
                {
                    'id': 'DEMO-121',
                    'title': 'Design dashboard mockups',
                    'status': 'Done',
                    'assignee': 'Maria Garcia',
                    'priority': 'Medium',
                    'story_points': 3
                },
                {
                    'id': 'DEMO-122',
                    'title': 'Set up CI/CD pipeline',
                    'status': 'In Progress',
                    'assignee': 'John Smith',
                    'priority': 'High',
                    'story_points': 8
                },
                {
                    'id': 'DEMO-123',
                    'title': 'API Integration with Payment Gateway',
                    'status': 'Blocked',
                    'assignee': 'Sarah Chen',
                    'priority': 'Critical',
                    'story_points': 13
                },
                {
                    'id': 'DEMO-124',
                    'title': 'Write API documentation',
                    'status': 'In Progress',
                    'assignee': 'David Lee',
                    'priority': 'Medium',
                    'story_points': 3
                }
            ],
            'last_updated': datetime.now().isoformat(),
            'data_source': 'demo',
            'demo_mode': True,
            'note': 'This is demo data. Configure Jira connection to see real project data.'
        }
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _execute(
        self,
        project_id: str,
        include_tasks: bool = True,
        sprint_scope: str = "current",
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Execute project status retrieval.
        
        Args:
            project_id: Project identifier (name, key, or ID)
            include_tasks: Include detailed task list
            sprint_scope: Which sprint(s) to query
            include_metrics: Include calculated metrics
            
        Returns:
            Project status data
        """
        logger.info(f"Fetching status for project: {project_id}")
        
        # Find project
        project = self.jira_client.find_project(project_id)
        if not project:
            # Return demo data instead of error for better demo experience
            logger.warning(f"Project '{project_id}' not found in Jira, using demo data")
            return self._generate_demo_data(project_id)
        
        # Get active sprint if needed
        sprint_id = None
        sprint_info = None
        if sprint_scope == "current":
            active_sprint = self.jira_client.get_active_sprint(project['key'])
            if active_sprint:
                sprint_id = active_sprint['id']
                sprint_info = {
                    'sprint_id': active_sprint['id'],
                    'sprint_name': active_sprint['name'],
                    'start_date': active_sprint.get('startDate'),
                    'end_date': active_sprint.get('endDate'),
                    'state': active_sprint.get('state')
                }
        
        # Fetch tasks/issues
        tasks = self.jira_client.get_project_tasks(
            project['key'],
            sprint_id=sprint_id
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(tasks) if include_metrics else {}
        
        # Identify blockers
        blockers = self._identify_blockers(tasks)
        
        # Determine overall status
        overall_status = self._determine_status(metrics, blockers)
        
        # Format tasks for output
        formatted_tasks = [self._format_task(task) for task in tasks] if include_tasks else []
        
        return {
            'success': True,
            'project_name': project['name'],
            'project_key': project['key'],
            'project_id': str(project['id']),
            'status': overall_status,
            'completion_percentage': metrics.get('completion_percentage', 0),
            'sprint_info': sprint_info,
            'metrics': metrics,
            'blockers': blockers,
            'tasks': formatted_tasks,
            'last_updated': datetime.now().isoformat(),
            'data_source': 'jira'
        }
    
    def _calculate_metrics(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Calculate project metrics from tasks."""
        total = len(tasks)
        if total == 0:
            return {'total_tasks': 0, 'completion_percentage': 0}
        
        completed = sum(1 for t in tasks if t.get('status') == 'Done')
        in_progress = sum(1 for t in tasks if t.get('status') == 'In Progress')
        blocked = sum(1 for t in tasks if 'blocked' in str(t.get('labels', [])).lower())
        todo = total - completed - in_progress - blocked
        
        completion_pct = (completed / total * 100) if total > 0 else 0
        
        # Calculate story points if available
        total_points = sum(t.get('story_points', 0) or 0 for t in tasks)
        completed_points = sum(
            t.get('story_points', 0) or 0 
            for t in tasks 
            if t.get('status') == 'Done'
        )
        
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'in_progress_tasks': in_progress,
            'blocked_tasks': blocked,
            'todo_tasks': todo,
            'completion_percentage': round(completion_pct, 1),
            'story_points': {
                'total': total_points,
                'completed': completed_points,
                'remaining': total_points - completed_points
            }
        }
    
    def _identify_blockers(self, tasks: List[Dict]) -> List[Dict[str, Any]]:
        """Identify and format blocked tasks."""
        blockers = []
        
        for task in tasks:
            is_blocked = (
                task.get('status') == 'Blocked' or
                'blocked' in str(task.get('labels', [])).lower()
            )
            
            if is_blocked:
                blockers.append({
                    'task_id': task.get('key'),
                    'task_title': task.get('summary'),
                    'blocker_reason': task.get('blocker_reason', 'No reason specified'),
                    'blocked_since': task.get('updated'),
                    'owner': task.get('assignee', {}).get('displayName', 'Unassigned'),
                    'severity': self._determine_blocker_severity(task)
                })
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        blockers.sort(key=lambda x: severity_order.get(x['severity'], 99))
        
        return blockers
    
    def _determine_blocker_severity(self, task: Dict) -> str:
        """Determine severity of a blocker."""
        priority = task.get('priority', {}).get('name', '').lower()
        
        if priority in ['highest', 'critical']:
            return 'critical'
        elif priority == 'high':
            return 'high'
        elif priority == 'medium':
            return 'medium'
        else:
            return 'low'
    
    def _determine_status(self, metrics: Dict, blockers: List) -> str:
        """Determine overall project status."""
        if not metrics:
            return 'unknown'
        
        completion = metrics.get('completion_percentage', 0)
        blocked_count = len(blockers)
        critical_blockers = sum(1 for b in blockers if b['severity'] == 'critical')
        
        if critical_blockers > 0 or blocked_count >= 3:
            return 'at_risk'
        elif completion >= 90:
            return 'on_track'
        elif completion >= 70 and blocked_count == 0:
            return 'on_track'
        elif blocked_count > 0:
            return 'at_risk'
        else:
            return 'on_track'
    
    def _format_task(self, task: Dict) -> Dict[str, Any]:
        """Format task data for output."""
        return {
            'id': task.get('key'),
            'title': task.get('summary'),
            'status': task.get('status'),
            'priority': task.get('priority', {}).get('name'),
            'assignee': task.get('assignee', {}).get('displayName', 'Unassigned'),
            'due_date': task.get('duedate'),
            'story_points': task.get('story_points'),
            'labels': task.get('labels', [])
        }