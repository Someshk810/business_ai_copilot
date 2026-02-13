"""
Jira API client for project management integration.
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from jira import JIRA
from jira.exceptions import JIRAError

from config.settings import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Client for interacting with Jira API.
    """
    
    def __init__(self):
        """Initialize Jira client."""
        try:
            self.jira = JIRA(
                server=JIRA_URL,
                basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
            )
            logger.info("Jira client initialized successfully")
        except JIRAError as e:
            logger.error(f"Failed to initialize Jira client: {str(e)}")
            raise
    
    def find_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by ID, key, or name.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Project data or None if not found
        """
        try:
            # Try exact match on key
            project = self.jira.project(project_id)
            return {
                'id': project.id,
                'key': project.key,
                'name': project.name
            }
        except JIRAError:
            pass
        
        # Try fuzzy match on name
        try:
            all_projects = self.jira.projects()
            for proj in all_projects:
                if project_id.lower() in proj.name.lower():
                    return {
                        'id': proj.id,
                        'key': proj.key,
                        'name': proj.name
                    }
        except JIRAError as e:
            logger.error(f"Error searching projects: {str(e)}")
        
        return None
    
    def get_active_sprint(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Get the active sprint for a project.
        
        Args:
            project_key: Project key
            
        Returns:
            Active sprint data or None
        """
        try:
            # Get board ID for project
            boards = self.jira.boards(projectKeyOrID=project_key)
            if not boards:
                return None
            
            board_id = boards[0].id
            
            # Get active sprints
            sprints = self.jira.sprints(board_id, state='active')
            if not sprints:
                return None
            
            sprint = sprints[0]
            return {
                'id': sprint.id,
                'name': sprint.name,
                'state': sprint.state,
                'startDate': getattr(sprint, 'startDate', None),
                'endDate': getattr(sprint, 'endDate', None)
            }
            
        except JIRAError as e:
            logger.warning(f"Could not get active sprint: {str(e)}")
            return None
    
    def get_project_tasks(
        self,
        project_key: str,
        sprint_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tasks for a project.
        
        Args:
            project_key: Project key
            sprint_id: Optional sprint ID to filter by
            
        Returns:
            List of task data
        """
        try:
            # Build JQL query
            jql = f'project = {project_key}'
            if sprint_id:
                jql += f' AND sprint = {sprint_id}'
            
            # Fetch issues
            issues = self.jira.search_issues(
                jql,
                maxResults=1000,
                fields='summary,status,priority,assignee,created,updated,duedate,labels,customfield_10016'  # customfield_10016 is story points
            )
            
            # Format tasks
            tasks = []
            for issue in issues:
                tasks.append({
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'priority': {
                        'name': issue.fields.priority.name if issue.fields.priority else 'None'
                    },
                    'assignee': {
                        'displayName': issue.fields.assignee.displayName if issue.fields.assignee else None
                    },
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'duedate': issue.fields.duedate,
                    'labels': issue.fields.labels,
                    'story_points': getattr(issue.fields, 'customfield_10016', None)
                })
            
            return tasks
            
        except JIRAError as e:
            logger.error(f"Error fetching tasks: {str(e)}")
            return []
    
    def get_project_suggestions(self, search_term: str) -> List[str]:
        """
        Get project name suggestions based on search term.
        
        Args:
            search_term: Partial project name
            
        Returns:
            List of suggested project names
        """
        try:
            all_projects = self.jira.projects()
            suggestions = [
                p.name for p in all_projects
                if search_term.lower() in p.name.lower()
            ]
            return suggestions[:5]  # Top 5 suggestions
        except JIRAError:
            return []