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
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
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
        workflow.add_node("generate_response", self.nodes.generate_response)
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
            return "generate_response"
        
        workflow.add_conditional_edges(
            "compose_email",
            should_handle_error,
            {
                "generate_response": "generate_response",
                "handle_error": "handle_error"
            }
        )
        
        # Both response and error handling end the workflow
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        # Compile workflow
        compiled = workflow.compile()
        
        logger.info("Workflow compiled successfully")
        return compiled
    
    def run(self, user_query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the workflow for a user query.
        
        Args:
            user_query: User's request
            user_context: Additional user context
            
        Returns:
            Final state with response
        """
        logger.info(f"Running workflow for query: {user_query}")
        
        # Create initial state
        initial_state = create_initial_state(user_query, user_context)
        
        # Execute workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            
            logger.info("Workflow completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            
            # Return error state
            return {
                'user_query': user_query,
                'final_response': f"I encountered an unexpected error: {str(e)}",
                'should_end': True,
                'tool_errors': [{'error': str(e)}]
            }