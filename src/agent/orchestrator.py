"""
LangGraph orchestrator for the agent workflow.
"""

from typing import Dict, Any
import logging

from langgraph.graph import StateGraph, END
from .state import AgentState, create_initial_state
from .nodes import WorkflowNodes

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the agent workflow using LangGraph.
    """
    
    def __init__(self, tools: Dict[str, Any]):
        """
        Initialize the orchestrator.
        
        Args:
            tools: Dictionary of available tools
        """
        self.tools = tools
        self.nodes = WorkflowNodes(tools)
        
        # Build both workflows
        self.status_email_workflow = self._build_status_email_workflow()
        self.priority_plan_workflow = self._build_priority_plan_workflow()
    
    def _build_status_email_workflow(self) -> StateGraph:
        """
        Build the status email workflow.
        
        Returns:
            Compiled workflow graph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", self.nodes.parse_intent)
        workflow.add_node("fetch_project_status", self.nodes.fetch_project_status)
        workflow.add_node("search_stakeholders", self.nodes.search_stakeholders)
        workflow.add_node("compose_email", self.nodes.compose_email)
        workflow.add_node("generate_plan_response", self.nodes.generate_plan_response)
        workflow.add_node("handle_error", self.nodes.handle_error)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("parse_intent")
        
        # After intent parsing, fetch project status
        workflow.add_edge("parse_intent", "fetch_project_status")
        
        # After fetching status, search for stakeholders (parallel-ready)
        workflow.add_edge("fetch_project_status", "search_stakeholders")
        
        # After stakeholders found, compose email
        workflow.add_edge("search_stakeholders", "compose_email")
        
        # After email composed, generate response or handle error
        def should_handle_error(state: AgentState) -> str:
            """Check if we should handle errors or generate response."""
            errors = state.get('tool_errors', [])
            # If critical errors, go to error handler
            if len(errors) > 2:
                return "handle_error"
            return "generate_plan_response"
        
        workflow.add_conditional_edges(
            "compose_email",
            should_handle_error,
            {
                "generate_plan_response": "generate_plan_response",
                "handle_error": "handle_error"
            }
        )
        
        # Both response and error handling end the workflow
        workflow.add_edge("generate_plan_response", END)
        workflow.add_edge("handle_error", END)
        
        # Compile workflow
        compiled = workflow.compile()
        
        logger.info("Workflow compiled successfully")
        return compiled
    
    def _build_priority_plan_workflow(self) -> StateGraph:
        """
        Build workflow for creating daily priority plan.
        
        Returns:
            Compiled workflow graph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", self.nodes.parse_intent)
        workflow.add_node("get_calendar_data", self.nodes.get_calendar_data)
        workflow.add_node("get_user_tasks", self.nodes.get_user_tasks)
        workflow.add_node("create_priority_plan", self.nodes.create_priority_plan)
        workflow.add_node("generate_plan_response", self.nodes.generate_plan_response)
        workflow.add_node("handle_error", self.nodes.handle_error)
        
        # Define workflow
        workflow.set_entry_point("parse_intent")
        
        # After intent, fetch calendar and tasks in parallel
        # Note: LangGraph doesn't have true parallel execution in this simple form,
        # but these could be run concurrently in production
        workflow.add_edge("parse_intent", "get_calendar_data")
        workflow.add_edge("get_calendar_data", "get_user_tasks")
        
        # After both data sources retrieved, create plan
        workflow.add_edge("get_user_tasks", "create_priority_plan")
        
        # After plan created, generate response
        def should_handle_error(state: AgentState) -> str:
            errors = state.get('tool_errors', [])
            if len(errors) > 2:
                return "handle_error"
            return "generate_plan_response"
        
        workflow.add_conditional_edges(
            "create_priority_plan",
            should_handle_error,
            {
                "generate_plan_response": "generate_plan_response",
                "handle_error": "handle_error"
            }
        )
        
        # End workflow
        workflow.add_edge("generate_plan_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def run(self, user_query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the appropriate workflow based on query.
        
        Args:
            user_query: User's request
            user_context: Additional user context
            
        Returns:
            Final state with response
        """
        logger.info(f"Running workflow for query: {user_query}")
        
        # Determine which workflow to use
        query_lower = user_query.lower()
        
        if any(keyword in query_lower for keyword in ['priority', 'plan', 'schedule', 'today']):
            workflow = self.priority_plan_workflow
            logger.info("Using priority plan workflow")
        else:
            workflow = self.status_email_workflow
            logger.info("Using status + email workflow")
        
        # Create initial state
        initial_state = create_initial_state(user_query, user_context)
        
        # Execute workflow
        try:
            final_state = workflow.invoke(initial_state)
            logger.info("Workflow completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            return {
                'user_query': user_query,
                'final_response': f"I encountered an unexpected error: {str(e)}",
                'should_end': True,
                'tool_errors': [{'error': str(e)}]
            }
