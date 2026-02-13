"""Input and data validators."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Validator:
    """Base validator class."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email address
            
        Returns:
            True if valid, False otherwise
        """
        # Simple validation - could be enhanced
        return "@" in email and "." in email
    
    @staticmethod
    def validate_project_data(project_data: Dict[str, Any]) -> bool:
        """Validate project data.
        
        Args:
            project_data: Project information
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["project_id", "name", "status"]
        return all(field in project_data for field in required_fields)
