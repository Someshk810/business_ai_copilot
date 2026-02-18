"""
LangGraph workflow nodes.
Each node represents a step in the agent's reasoning/execution process.
"""

from typing import Dict, Any
import logging
import json
from datetime import datetime

from anthropic import Anthropic
from .state import AgentState
# NEW
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config.settings import GOOGLE_API_KEY, DEFAULT_MODEL, MAX_TOKENS, DEFAULT_TEMPERATURE

from config.prompts import SYSTEM_PROMPT, INTENT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class WorkflowNodes:
    """
    Collection of nodes for the LangGraph workflow.
    Each method is a node that processes and updates state.
    """
  
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.llm = ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=DEFAULT_TEMPERATURE,
            max_output_tokens=MAX_TOKENS
        )
    
    def parse_intent(self, state: AgentState) -> AgentState:
        """
        Analyze user intent and plan the workflow.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent analysis
        """
        logger.info("Node: parse_intent")
        
        try:
            # Build prompt for intent analysis
            prompt = INTENT_ANALYSIS_PROMPT.format(
                user_query=state['user_query']
            )
            


            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            if isinstance(response, str):
                content = response
            else:
                content = response.content if hasattr(response, 'content') else str(response)
            # content = response.content
            
            # # Parse response
            # content = response.content[0].text
            
            # Try to extract JSON
            try:
                intent_data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("Could not parse intent as JSON, using basic analysis")
                intent_data = {
                    'intent': 'multi_step_workflow',
                    'entities': {'project': 'Phoenix'},
                    'required_tools': ['get_project_status', 'knowledge_search', 'compose_email'],
                    'confidence': 0.8
                }
            
            # Update state
            state['intent_analysis'] = intent_data
            state['confidence_score'] = intent_data.get('confidence', 0.8)
            state['step'] = 'intent_parsed'
            
            logger.info(f"Intent parsed: {intent_data.get('intent')}")
            
        except Exception as e:
            logger.error(f"Intent parsing failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'parse_intent',
                'error': str(e)
            })
        
        return state
    
    def fetch_project_status(self, state: AgentState) -> AgentState:
        """
        Fetch project status from Jira.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with project status
        """
        logger.info("Node: fetch_project_status")
        
        try:
            # Extract project from intent
            intent = state.get('intent_analysis', {})
            entities = intent.get('entities', {})
            project_id = entities.get('project', 'Phoenix')  # Default to Phoenix for demo
            
            # Call tool
            project_status_tool = self.tools['get_project_status']
            result = project_status_tool.execute(
                project_id=project_id,
                include_tasks=True,
                sprint_scope='current',
                include_metrics=True
            )
            
            # Store result
            state['project_status'] = result
            state['tool_outputs']['get_project_status'] = result
            state['tools_called'].append('get_project_status')
            
            if result.get('success'):
                logger.info(f"Project status fetched: {result.get('status')}")
            else:
                logger.warning(f"Project status fetch failed: {result.get('error')}")
                state['tool_errors'].append({
                    'tool': 'get_project_status',
                    'error': result.get('message')
                })
        
        except Exception as e:
            logger.error(f"Project status fetch failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'fetch_project_status',
                'error': str(e)
            })
        
        state['step'] = 'project_status_fetched'
        return state
    
    def search_stakeholders(self, state: AgentState) -> AgentState:
        """
        Search knowledge base for stakeholder information.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with stakeholder data
        """
        logger.info("Node: search_stakeholders")
        
        try:
            # Determine project name
            project_status = state.get('project_status', {})
            project_name = project_status.get('project_name', 'Phoenix')
            
            # Build search query
            query = f"{project_name} stakeholders team members"
            
            # Call tool
            knowledge_tool = self.tools['knowledge_search']
            result = knowledge_tool.execute(
                query=query,
                top_k=3,
                filters={'project': project_name.split()[0]}  # "Project Phoenix" -> "Phoenix"
            )
            
            # Extract stakeholder information
            stakeholders = []
            if result.get('success') and result.get('results'):
                for doc in result['results']:
                    content = doc.get('content', '')
                    # Simple extraction - look for email patterns
                    import re
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', content)
                    names = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+)', content)
                    
                    for name in names[:5]:  # Top 5 names
                        stakeholders.append({
                            'name': name,
                            'email': emails[0] if emails else f"{name.lower().replace(' ', '.')}@company.com"
                        })
                
                # Deduplicate
                seen = set()
                unique_stakeholders = []
                for s in stakeholders:
                    if s['name'] not in seen:
                        seen.add(s['name'])
                        unique_stakeholders.append(s)
                
                stakeholders = unique_stakeholders
            
            # Store result
            state['stakeholders'] = stakeholders
            state['tool_outputs']['knowledge_search'] = result
            state['tools_called'].append('knowledge_search')
            
            logger.info(f"Found {len(stakeholders)} stakeholders")
        
        except Exception as e:
            logger.error(f"Stakeholder search failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'search_stakeholders',
                'error': str(e)
            })
            # Use default stakeholders
            state['stakeholders'] = [
                {'name': 'Sarah Chen', 'email': 'sarah.chen@company.com'},
                {'name': 'Michael Rodriguez', 'email': 'michael.r@company.com'}
            ]
        
        state['step'] = 'stakeholders_found'
        return state
    
    def compose_email(self, state: AgentState) -> AgentState:
        """
        Compose status update email.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with email draft
        """
        logger.info("Node: compose_email")
        
        try:
            # Get data from previous steps
            project_status = state.get('project_status', {})
            stakeholders = state.get('stakeholders', [])
            
            # Build key points from project status
            key_points = []
            
            if project_status.get('success'):
                completion = project_status.get('completion_percentage', 0)
                status = project_status.get('status', 'unknown')
                metrics = project_status.get('metrics', {})
                blockers = project_status.get('blockers', [])
                
                key_points.append(
                    f"Project is {completion}% complete "
                    f"({metrics.get('completed_tasks', 0)} of {metrics.get('total_tasks', 0)} tasks done)"
                )
                
                key_points.append(f"Status: {status.replace('_', ' ').title()}")
                
                if blockers:
                    key_points.append(f"{len(blockers)} blocking issues identified")
                    for blocker in blockers[:3]:  # Top 3 blockers
                        key_points.append(
                            f"{blocker['severity'].title()} blocker: {blocker['task_title']} "
                            f"(owner: {blocker['owner']})"
                        )
                
                sprint_info = project_status.get('sprint_info', {})
                if sprint_info:
                    key_points.append(
                        f"Sprint {sprint_info.get('sprint_name', 'current')}: "
                        f"in progress"
                    )
            else:
                key_points.append("Project status could not be retrieved")
            
            # Format recipients
            recipients = [
                {'name': s['name'], 'email': s['email'], 'role': 'Stakeholder'}
                for s in stakeholders[:4]  # Top 4 stakeholders
            ]
            
            # Determine tone based on status
            tone = "formal"
            if project_status.get('status') == 'at_risk':
                tone = "urgent"
            
            # Call email composer tool
            email_tool = self.tools['compose_email']
            result = email_tool.execute(
                purpose=f"Weekly status update for {project_status.get('project_name', 'project')}",
                key_points=key_points,
                recipients=recipients,
                tone=tone,
                include_action_items=True
            )
            
            # Store result
            state['email_draft'] = result
            state['tool_outputs']['compose_email'] = result
            state['tools_called'].append('compose_email')
            
            if result.get('subject'):
                logger.info(f"Email composed: {result['subject']}")
            else:
                logger.warning("Email composition returned no subject")
        
        except Exception as e:
            logger.error(f"Email composition failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'compose_email',
                'error': str(e)
            })
        
        state['step'] = 'email_composed'
        return state
    
    def generate_email_status_response(self, state: AgentState) -> AgentState:
        """
        Generate final response for status + email workflow.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final response
        """
        logger.info("Node: generate_email_status_response")
        
        try:
            # Get data from previous steps
            project_status = state.get('project_status', {})
            email_draft = state.get('email_draft', {})
            stakeholders = state.get('stakeholders', [])
            
            response_parts = []
            response_parts.append("# 📊 Project Status & Email Update\n")
            
            # Project Status Section
            response_parts.append("## 🚀 Project Status\n")
            
            # Check if we have an error response (no 'error' key means success)
            if project_status and 'error' not in project_status:
                project_name = project_status.get('project_name', 'Unknown Project')
                completion = project_status.get('completion_percentage', 0)
                status = project_status.get('status', 'unknown').replace('_', ' ').title()
                metrics = project_status.get('metrics', {})
                is_demo = project_status.get('demo_mode', False)
                
                # Add demo indicator if using demo data
                if is_demo:
                    response_parts.append("*🎭 Demo Mode: Showing sample data (Jira project not found)*\n")
                
                response_parts.append(f"**Project:** {project_name}")
                response_parts.append(f"**Status:** {status}")
                response_parts.append(f"**Completion:** {completion}%")
                response_parts.append(f"**Tasks:** {metrics.get('completed_tasks', 0)}/{metrics.get('total_tasks', 0)} completed\n")
                
                # Blockers
                blockers = project_status.get('blockers', [])
                if blockers:
                    response_parts.append("### ⚠️ Blockers\n")
                    for blocker in blockers[:5]:
                        response_parts.append(
                            f"- **{blocker.get('severity', 'medium').upper()}**: {blocker.get('task_title', 'Unknown')} "
                            f"(Owner: {blocker.get('owner', 'Unassigned')})"
                        )
                    response_parts.append("")
                
                # Sprint info
                sprint_info = project_status.get('sprint_info', {})
                if sprint_info:
                    response_parts.append("### 📅 Current Sprint\n")
                    response_parts.append(f"**Sprint:** {sprint_info.get('sprint_name', 'Current')}")
                    response_parts.append(f"**Progress:** {sprint_info.get('completed_points', 0)}/{sprint_info.get('total_points', 0)} points")
                    response_parts.append("")
            else:
                # Show error message with helpful context
                error_msg = project_status.get('message', 'Unknown error') if project_status else 'No data available'
                response_parts.append(f"⚠️ Could not retrieve project status from Jira")
                response_parts.append(f"**Error:** {error_msg}")
                
                # Show suggestions if available
                suggestions = project_status.get('suggestions', []) if project_status else []
                if suggestions:
                    response_parts.append(f"\n**Available projects:** {', '.join(suggestions)}")
                response_parts.append("\n*Note: This is a demo system. To see real data, configure Jira with actual project details.*\n")
            
            # Email Draft Section
            response_parts.append("## 📧 Email Draft\n")
            
            if email_draft and not email_draft.get('error'):
                subject = email_draft.get('subject', 'No subject')
                body = email_draft.get('body', 'No content')
                
                if len(stakeholders) > 3:
                    response_parts.append(f"**To:** {', '.join(s.get('name', 'Unknown') for s in stakeholders[:3])} and {len(stakeholders) - 3} others")
                elif stakeholders:
                    response_parts.append(f"**To:** {', '.join(s.get('name', 'Unknown') for s in stakeholders)}")
                else:
                    response_parts.append("**To:** Project Stakeholders")
                    
                response_parts.append(f"**Subject:** {subject}\n")
                response_parts.append("**Body:**")
                response_parts.append("```")
                response_parts.append(body)
                response_parts.append("```\n")
            else:
                response_parts.append("⚠️ Email composition encountered an error")
                if email_draft:
                    response_parts.append(f"Error: {email_draft.get('message', 'Unknown error')}")
                    # Show fallback if available
                    if email_draft.get('subject') and email_draft.get('body'):
                        response_parts.append("\n**Fallback Draft:**")
                        response_parts.append(f"**Subject:** {email_draft.get('subject')}")
                        response_parts.append(f"**Body:** {email_draft.get('body')}")
                response_parts.append("")
            
            # Next steps
            response_parts.append("## ⚡ Next Steps\n")
            response_parts.append("• Review and edit the email draft")
            response_parts.append("• Send to stakeholders")
            response_parts.append("• Address blocking issues")
            response_parts.append("• Schedule follow-up")
            
            final_response = "\n".join(response_parts)
            
            state['final_response'] = final_response
            state['should_end'] = True
            state['end_time'] = datetime.now()
            
            logger.info("Email status response generated")
        
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}", exc_info=True)
            state['final_response'] = f"I encountered an error while creating the response: {str(e)}"
            state['should_end'] = True
        
        return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """
        Generate final response to user.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final response
        """
        logger.info("Node: generate_response")
        
        try:
            project_status = state.get('project_status', {})
            email_draft = state.get('email_draft', {})
            stakeholders = state.get('stakeholders', [])
            
            # Build response
            response_parts = []
            
            # Status summary
            if project_status.get('success'):
                status = project_status.get('status', 'unknown')
                completion = project_status.get('completion_percentage', 0)
                metrics = project_status.get('metrics', {})
                blockers = project_status.get('blockers', [])
                
                response_parts.append("✓ I've retrieved the current status for Project Phoenix and drafted an update email.\n")
                response_parts.append("📊 **Project Status Summary:**")
                response_parts.append(f"• Overall Status: {status.replace('_', ' ').title()}")
                response_parts.append(f"• Completion: {completion}% ({metrics.get('completed_tasks', 0)}/{metrics.get('total_tasks', 0)} tasks)")
                
                if blockers:
                    response_parts.append(f"• Blockers: {len(blockers)} issues")
                    for blocker in blockers[:2]:
                        response_parts.append(
                            f"  - {blocker['task_title']} ({blocker['severity']})"
                        )
                
                response_parts.append("")
            
            # Email draft
            if email_draft.get('subject'):
                response_parts.append("📧 **Draft Email:**\n")
                response_parts.append(f"**To:** {', '.join(s['name'] for s in stakeholders[:4])}")
                response_parts.append(f"**Subject:** {email_draft['subject']}\n")
                response_parts.append(f"{email_draft['body']}\n")
                response_parts.append("---\n")
            
            # Next actions
            response_parts.append("**What would you like to do?**")
            response_parts.append("• Send the email now")
            response_parts.append("• Edit the draft")
            response_parts.append("• Change recipients")
            response_parts.append("• Get more details on blockers")
            
            final_response = "\n".join(response_parts)
            
            state['final_response'] = final_response
            state['should_end'] = True
            state['end_time'] = datetime.now()
            
            logger.info("Final response generated")
        
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}", exc_info=True)
            state['final_response'] = f"I encountered an error while processing your request: {str(e)}"
            state['should_end'] = True
        
        return state
    
    def handle_error(self, state: AgentState) -> AgentState:
        """
        Handle errors and generate error response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with error response
        """
        logger.info("Node: handle_error")
        
        errors = state.get('tool_errors', [])
        
        error_messages = []
        for error in errors:
            error_messages.append(f"- {error.get('step', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
        response = "I encountered some issues while processing your request:\n\n"
        response += "\n".join(error_messages)
        response += "\n\nWould you like me to try again or help with something else?"
        
        state['final_response'] = response
        state['should_end'] = True
        state['end_time'] = datetime.now()
        
        return state
    
    def get_calendar_data(self, state: AgentState) -> AgentState:
        """
        Retrieve today's calendar events.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with calendar data
        """
        logger.info("Node: get_calendar_data")
        
        try:
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Call calendar tool
            calendar_tool = self.tools.get('manage_calendar')
            if not calendar_tool:
                raise ValueError("Calendar tool not available")
            
            result = calendar_tool.execute(
                action='get_events',
                date='today'
            )
            
            # Store result
            state['calendar_data'] = result
            state['tool_outputs']['manage_calendar'] = result
            state['tools_called'].append('manage_calendar')
            
            if result.get('success'):
                event_count = len(result.get('events', []))
                logger.info(f"Retrieved {event_count} calendar events")
            else:
                logger.warning("Calendar retrieval failed")
                state['tool_errors'].append({
                    'tool': 'manage_calendar',
                    'error': result.get('message', 'Unknown error')
                })
        
        except Exception as e:
            logger.error(f"Calendar retrieval failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'get_calendar_data',
                'error': str(e)
            })
            # Use empty calendar as fallback
            state['calendar_data'] = {
                'success': True,
                'events': [],
                'free_blocks': []
            }
        
        state['step'] = 'calendar_retrieved'
        return state


    def get_user_tasks(self, state: AgentState) -> AgentState:
        """
        Retrieve user's open tasks.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with task data
        """
        logger.info("Node: get_user_tasks")
        
        try:
            # Get user context
            user_context = state.get('user_context', {})
            user_email = user_context.get('user_email', 'john.doe@company.com')
            
            # Call task manager tool
            task_tool = self.tools.get('manage_tasks')
            if not task_tool:
                raise ValueError("Task manager tool not available")
            
            result = task_tool.execute(
                action='get_my_tasks',
                user_email=user_email,
                filters={'status': ['todo', 'in_progress']},
                sort_by='due_date'
            )
            
            # Debug logging
            logger.debug(f"Task tool result type: {type(result)}")
            logger.debug(f"Task tool result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            if isinstance(result, dict) and 'tasks' in result:
                logger.debug(f"Number of tasks in result: {len(result['tasks'])}")
            
            # Store result - Make sure it's in the right format
            state['user_tasks'] = result
            state['tool_outputs']['manage_tasks'] = result
            state['tools_called'].append('manage_tasks')
            
            if result.get('success'):
                task_count = result.get('total_count', 0)
                tasks_list = result.get('tasks', [])
                logger.info(f"Retrieved {task_count} open tasks (actual list: {len(tasks_list)} items)")
                
                # Additional debug - log first task if available
                if tasks_list:
                    logger.debug(f"First task sample: {tasks_list[0].get('id', 'no-id')} - {tasks_list[0].get('title', 'no-title')}")
            else:
                logger.warning("Task retrieval failed")
                state['tool_errors'].append({
                    'tool': 'manage_tasks',
                    'error': result.get('message', 'Unknown error')
                })
        
        except Exception as e:
            logger.error(f"Task retrieval failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'get_user_tasks',
                'error': str(e)
            })
            # Use empty task list as fallback
            state['user_tasks'] = {
                'success': True,
                'tasks': [],
                'total_count': 0
            }
        
        state['step'] = 'tasks_retrieved'
        return state
    
    def create_priority_plan(self, state: AgentState) -> AgentState:
        """
        Create prioritized daily plan.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with priority plan
        """
        logger.info("Node: create_priority_plan")
        
        try:
            # Get data from previous steps
            calendar_data = state.get('calendar_data', {})
            task_data = state.get('user_tasks', {})
            user_context = state.get('user_context', {})
            
            # Debug: Log what we received
            logger.debug(f"Calendar data type: {type(calendar_data)}")
            logger.debug(f"Calendar data content: {calendar_data}")
            logger.debug(f"Task data type: {type(task_data)}")
            logger.debug(f"Task data keys: {task_data.keys() if isinstance(task_data, dict) else 'not a dict'}")
            logger.debug(f"Task data content: {task_data}")
            
            # Extract tasks and calendar info with validation
            tasks = []
            if isinstance(task_data, dict):
                tasks = task_data.get('tasks', [])
                logger.debug(f"Extracted {len(tasks)} tasks from task_data")
                if tasks:
                    logger.debug(f"First task: {tasks[0]}")
            else:
                logger.warning(f"task_data is not a dict, it's: {type(task_data)}")
            
            events = []
            free_blocks = []
            if isinstance(calendar_data, dict):
                events = calendar_data.get('events', [])
                free_blocks = calendar_data.get('free_blocks', [])
                logger.debug(f"Extracted {len(events)} events and {len(free_blocks)} free blocks")
                if events:
                    logger.debug(f"First event: {events[0]}")
            else:
                logger.warning(f"calendar_data is not a dict, it's: {type(calendar_data)}")
            
            # Log counts
            logger.info(f"Processing {len(tasks)} tasks, {len(events)} events, {len(free_blocks)} free blocks")
            
            # Verify data is actually present
            if len(tasks) == 0:
                logger.error(f"No tasks extracted! State user_tasks: {state.get('user_tasks')}")
            if len(events) == 0:
                logger.warning(f"No events extracted! State calendar_data: {state.get('calendar_data')}")
            
            # Verify data is actually present
            if len(tasks) == 0:
                logger.error(f"No tasks extracted! State user_tasks: {state.get('user_tasks')}")
            if len(events) == 0:
                logger.warning(f"No events extracted! State calendar_data: {state.get('calendar_data')}")
            
            # Get user preferences
            user_preferences = user_context.get('preferences', {
                'morning_focus': True,
                'prefer_long_blocks': True
            })
            
            # Call priority planner tool
            planner_tool = self.tools.get('create_priority_plan')
            if not planner_tool:
                raise ValueError("Priority planner tool not available")
            
            result = planner_tool.execute(
                tasks=tasks,
                calendar_events=events,
                free_blocks=free_blocks,
                user_preferences=user_preferences
            )
            
            # Store result
            state['priority_plan'] = result
            state['tool_outputs']['create_priority_plan'] = result
            state['tools_called'].append('create_priority_plan')
            
            if result.get('success'):
                scheduled_count = len(result.get('schedule', []))
                logger.info(f"Created plan with {scheduled_count} scheduled tasks")
            else:
                logger.warning("Priority planning failed")
        
        except Exception as e:
            logger.error(f"Priority planning failed: {str(e)}", exc_info=True)
            state['tool_errors'].append({
                'step': 'create_priority_plan',
                'error': str(e)
            })
        
        state['step'] = 'plan_created'
        return state
    
    def generate_plan_response(self, state: AgentState) -> AgentState:
        """
        Generate final priority plan response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final response
        """
        logger.info("Node: generate_plan_response")
        
        try:
            calendar_data = state.get('calendar_data', {})
            task_data = state.get('user_tasks', {})
            priority_plan = state.get('priority_plan', {})
            
            # Build response
            response_parts = []
            
            # Header
            today = datetime.now().strftime('%A, %B %d, %Y')
            response_parts.append(f"# 🗓️ Daily Priority Plan - {today}\n")
            
            # Overview
            summary = priority_plan.get('summary', {})
            response_parts.append("## 📊 Overview\n")
            response_parts.append(f"**Total Tasks:** {summary.get('total_tasks', 0)}")
            response_parts.append(f"**High Priority:** {summary.get('high_priority_count', 0)}")
            response_parts.append(f"**Meetings:** {summary.get('total_meeting_time', 0)} minutes")
            response_parts.append(f"**Available Time:** {summary.get('total_free_time', 0)} minutes\n")
            
            # Top Priorities
            response_parts.append("## 🎯 Top Priorities\n")
            prioritized_tasks = priority_plan.get('prioritized_tasks', [])
            for i, task in enumerate(prioritized_tasks[:5], 1):
                priority_emoji = '⚠️' if task.get('priority') == 'critical' else '🔴' if task.get('priority') == 'high' else '🟡'
                response_parts.append(
                    f"{i}. {priority_emoji} **{task['title']}** (Score: {task.get('priority_score', 0)})"
                )
                response_parts.append(f"   - Project: {task.get('project', 'Unknown')}")
                response_parts.append(f"   - Due: {task.get('due_date', 'No deadline')}")
                if task.get('blocked'):
                    response_parts.append(f"   - ⚠️ BLOCKED: {task.get('blocker_reason', 'Unknown')}")
                response_parts.append("")
            
            # Schedule
            response_parts.append("## 📅 Your Schedule\n")
            schedule = priority_plan.get('schedule', [])
            events = calendar_data.get('events', [])
            
            # Combine and sort by time
            all_items = []
            for event in events:
                all_items.append({
                    'type': 'meeting',
                    'time': event['start_time'],
                    'data': event
                })
            for item in schedule:
                all_items.append({
                    'type': 'task',
                    'time': item['start_time'],
                    'data': item
                })
            
            all_items.sort(key=lambda x: x['time'])
            
            current_hour = None
            for item in all_items:
                item_time = datetime.fromisoformat(item['time'])
                hour = item_time.strftime('%I:%M %p')
                
                if item['type'] == 'meeting':
                    event = item['data']
                    end_time = datetime.fromisoformat(event['end_time']).strftime('%I:%M %p')
                    response_parts.append(f"**{hour} - {end_time}:** 📞 {event['title']}")
                else:
                    task = item['data']
                    end_time = datetime.fromisoformat(task['end_time']).strftime('%I:%M %p')
                    response_parts.append(
                        f"**{hour} - {end_time}:** 🎯 {task['task_title']} "
                        f"({task['block_type'].replace('_', ' ').title()})"
                    )
            
            response_parts.append("")
            
            # Suggestions
            suggestions = priority_plan.get('suggestions', [])
            if suggestions:
                response_parts.append("## 💡 Suggestions\n")
                for suggestion in suggestions:
                    response_parts.append(f"• {suggestion}")
                response_parts.append("")
            
            # Next actions
            response_parts.append("## ⚡ Quick Actions\n")
            response_parts.append("• View detailed task breakdown")
            response_parts.append("• Reschedule meetings for more focus time")
            response_parts.append("• Mark tasks as complete")
            response_parts.append("• Get help with blockers")
            
            final_response = "\n".join(response_parts)
            
            state['final_response'] = final_response
            state['should_end'] = True
            state['end_time'] = datetime.now()
            
            logger.info("Priority plan response generated")
        
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}", exc_info=True)
            state['final_response'] = f"I encountered an error while creating your plan: {str(e)}"
            state['should_end'] = True
        
        return state