"""
State management for the LangGraph agent.
"""

from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State schema for the agent workflow.
    
    This tracks all information as the agent progresses through
    the workflow, including messages, tool outputs, and decisions.
    """
    
    # User input and conversation
    user_query: str
    user_context: Dict[str, Any]
    current_time: datetime
    
    # Workflow tracking
    workflow_id: str
    step: str
    iteration: int
    max_iterations: int
    
    # Tool execution results
    tool_outputs: Annotated[Dict[str, Any], operator.or_]
    tool_errors: Annotated[list, operator.add]
    
    # Intermediate results
    project_status: Optional[Dict[str, Any]]
    stakeholders: Optional[list]
    email_draft: Optional[Dict[str, Any]]
    calendar_data: Optional[Dict[str, Any]]
    user_tasks: Optional[Dict[str, Any]]
    priority_plan: Optional[Dict[str, Any]]
    
    # Planning and reasoning
    intent_analysis: Optional[Dict[str, Any]]
    execution_plan: Optional[Dict[str, Any]]
    
    # Validation
    validation_results: Optional[Dict[str, Any]]
    confidence_score: float
    
    # Final output
    final_response: Optional[str]
    should_end: bool
    
    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    total_tokens_used: int
    tools_called: Annotated[list, operator.add]


def create_initial_state(user_query: str, user_context: Dict[str, Any] = None) -> AgentState:
    """
    Create initial state for a new workflow.
    
    Args:
        user_query: The user's request
        user_context: Additional context about the user
        
    Returns:
        Initial AgentState
    """
    import uuid
    
    return AgentState(
        user_query=user_query,
        user_context=user_context or {},
        current_time=datetime.now(),
        workflow_id=str(uuid.uuid4()),
        step="start",
        iteration=0,
        max_iterations=10,
        tool_outputs={},
        tool_errors=[],
        project_status=None,
        stakeholders=None,
        email_draft=None,
        calendar_data=None,
        user_tasks=None,
        priority_plan=None,
        intent_analysis=None,
        execution_plan=None,
        validation_results=None,
        confidence_score=0.0,
        final_response=None,
        should_end=False,
        start_time=datetime.now(),
        end_time=None,
        total_tokens_used=0,
        tools_called=[]
    )