"""
Main entry point for the Business AI Copilot.
"""

import logging
from typing import Optional

from config.settings import GOOGLE_API_KEY, JIRA_URL
from src.utils.logging_config import setup_logging
from src.integrations.jira_client import JiraClient
from src.integrations.vector_db import VectorDatabase
from src.tools.project_status import ProjectStatusTool
from src.tools.knowledge_search import KnowledgeSearchTool
from src.tools.email_composer import EmailComposerTool
from src.tools.calender_manager import CalendarManagerTool
from src.tools.task_manager import TaskManagerTool
from src.tools.priority_planner import PriorityPlannerTool
from src.agent.orchestrator import AgentOrchestrator

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class BusinessCopilot:
    """
    Main Business AI Copilot application.
    """

    def __init__(self):
        """Initialize the copilot with all dependencies."""
        logger.info("Initializing Business AI Copilot...")
        
        # Check required configuration
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set in environment")
        
        # Initialize integrations
        self.jira_client = None
        if JIRA_URL:
            try:
                self.jira_client = JiraClient()
                logger.info("Jira integration initialized")
            except Exception as e:
                logger.warning(f"Jira integration failed: {str(e)}")
        
        self.vector_db = VectorDatabase()
        logger.info("Vector database initialized")
        
        # Initialize tools
        self.tools = {}
        
        # Original tools
        if self.jira_client:
            self.tools['get_project_status'] = ProjectStatusTool(self.jira_client)
        
        self.tools['knowledge_search'] = KnowledgeSearchTool(self.vector_db)
        self.tools['compose_email'] = EmailComposerTool()
        
        # NEW: Priority planning tools
        self.tools['manage_calendar'] = CalendarManagerTool()
        self.tools['manage_tasks'] = TaskManagerTool(self.jira_client)
        self.tools['create_priority_plan'] = PriorityPlannerTool()
        
        logger.info(f"Initialized {len(self.tools)} tools")
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(self.tools)
        logger.info("Orchestrator initialized")
        
        logger.info("Business AI Copilot ready!")
    
    def process_query(self, query: str, user_context: Optional[dict] = None) -> str:
        """
        Process a user query and return response.
        
        Args:
            query: User's request
            user_context: Optional user context
            
        Returns:
            Response text
        """
        logger.info(f"Processing query: {query}")
        
        # Run workflow
        result = self.orchestrator.run(query, user_context)
        
        # Extract response
        response = result.get('final_response', 'I was unable to process your request.')
        
        # Log metrics
        tools_called = result.get('tools_called', [])
        errors = result.get('tool_errors', [])
        
        logger.info(f"Query completed. Tools called: {len(tools_called)}, Errors: {len(errors)}")
        
        return response


def main():
    """Main function for CLI usage."""
    import sys
    
    print("🤖 Business AI Copilot")
    print("=" * 50)
    print()
    
    # Initialize copilot
    try:
        copilot = BusinessCopilot()
    except Exception as e:
        print(f"❌ Failed to initialize copilot: {str(e)}")
        return 1
    
    # Check if query provided as argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}")
        print()
        
        response = copilot.process_query(query)
        print(response)
        return 0
    
    # Interactive mode
    print("Interactive mode. Type 'exit' to quit.")
    print()
    
    while True:
        try:
            query = input("You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            print()
            print("Agent:")
            response = copilot.process_query(query)
            print(response)
            print()
            print("-" * 50)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            print(f"❌ Error: {str(e)}")
            print()
    
    return 0


if __name__ == "__main__":
    exit(main())