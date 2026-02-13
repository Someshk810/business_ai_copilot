"""
Email composition tool using Claude.
"""

from typing import Dict, Any, List
import logging
import json

from .base import BaseTool
from anthropic import Anthropic
from config.settings import ANTHROPIC_API_KEY, DEFAULT_MODEL
from config.prompts import EMAIL_COMPOSITION_PROMPT

logger = logging.getLogger(__name__)


class EmailComposerTool(BaseTool):
    """
    Tool for composing professional emails.
    """
    
    def __init__(self):
        super().__init__(
            name="compose_email",
            description="Draft professional emails with appropriate tone and structure"
        )
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.cache_ttl = 0  # Don't cache email compositions
    
    def _execute(
        self,
        purpose: str,
        key_points: List[str],
        recipients: List[Dict[str, str]] = None,
        tone: str = "formal",
        include_action_items: bool = False
    ) -> Dict[str, Any]:
        """
        Compose an email.
        
        Args:
            purpose: What the email is about
            key_points: Main information to include
            recipients: List of recipient details
            tone: Email tone (formal, casual, urgent)
            include_action_items: Include action items section
            
        Returns:
            Email draft with subject and body
        """
        logger.info(f"Composing email: {purpose}")
        
        # Format key points
        key_points_text = "\n".join(f"- {point}" for point in key_points)
        
        # Format recipients
        recipients_text = "General stakeholders"
        if recipients:
            recipients_text = ", ".join(
                f"{r.get('name', 'Unknown')} ({r.get('role', 'Team Member')})"
                for r in recipients
            )
        
        # Build prompt
        prompt = EMAIL_COMPOSITION_PROMPT.format(
            purpose=purpose,
            key_points=key_points_text,
            recipients=recipients_text,
            tone=tone,
            include_action_items=include_action_items
        )
        
        # Call Claude
        try:
            response = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=2000,
                temperature=0.3,  # Lower for consistent formatting
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Try to parse as JSON
            try:
                email_data = json.loads(content)
            except json.JSONDecodeError:
                # Extract from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                    email_data = json.loads(json_str)
                else:
                    raise ValueError("Could not parse email response as JSON")
            
            # Add metadata
            email_data['metadata'] = {
                'tone': tone,
                'word_count': len(email_data['body'].split()),
                'recipients_count': len(recipients) if recipients else 0
            }
            
            return email_data
            
        except Exception as e:
            logger.error(f"Email composition failed: {str(e)}")
            return {
                'error': 'composition_failed',
                'message': f"Failed to compose email: {str(e)}",
                'subject': '',
                'body': ''
            }