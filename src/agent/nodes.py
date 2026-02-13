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
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL, MAX_TOKENS, DEFAULT_TEMPERATURE
from config.prompts import SYSTEM_PROMPT, INTENT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class WorkflowNodes:
    """
    Collection of nodes for the LangGraph workflow.
    Each method is a node that processes and updates state.
    """
    
    def __init__(self, tools: Dict[str, Any]):
        """
        Initialize workflow nodes.
        
        Args:
            tools: Dictionary of available tools
        """
        self.tools = tools
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
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
            
            # Call Claude for intent analysis
            response = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=2000,
                temperature=DEFAULT_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Try to extract JSON
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                    intent_data = json.loads(json_str)
                else:
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