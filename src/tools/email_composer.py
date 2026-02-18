

"""
Email composition tool using Google Gemini.
"""

from typing import Dict, Any, List, Optional
import logging
import json

from .base import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config.settings import GOOGLE_API_KEY, DEFAULT_MODEL
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
        self.llm = ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3,
            max_output_tokens=2000
        )
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
        
        # Call Gemini
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            # Handle response - LangChain returns AIMessage object
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            logger.debug(f"LLM response type: {type(response)}")
            logger.debug(f"Content preview: {content[:200]}")
            
            # Try multiple parsing strategies
            email_data = None
            
            # Strategy 1: Direct JSON parse
            try:
                email_data = json.loads(content)
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Extract from markdown code blocks
            if not email_data and "```" in content:
                try:
                    # Try ```json first
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                    else:
                        json_start = content.find("```") + 3
                    
                    json_end = content.find("```", json_start)
                    if json_end > json_start:
                        json_str = content[json_start:json_end].strip()
                        email_data = json.loads(json_str)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Markdown block parsing failed: {e}")
            
            # Strategy 3: Manual extraction as fallback
            if not email_data:
                logger.warning("JSON parsing failed, using regex extraction")
                import re
                
                # Try to extract subject and body using patterns
                subject_match = re.search(r'["\']subject["\']\s*:\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
                body_match = re.search(r'["\']body["\']\s*:\s*["\']([^"\']+)["\']', content, re.IGNORECASE | re.DOTALL)
                
                if not subject_match or not body_match:
                    # Try multiline body with triple quotes
                    body_match = re.search(r'["\']body["\']\s*:\s*"""([^"]+?)"""', content, re.DOTALL)
                
                if subject_match:
                    email_data = {
                        'subject': subject_match.group(1),
                        'body': body_match.group(1) if body_match else content
                    }
                else:
                    # Last resort: use content as body
                    email_data = {
                        'subject': f"Update: {purpose}",
                        'body': content
                    }
            
            # Validate required fields
            if 'subject' not in email_data or 'body' not in email_data:
                logger.error(f"Missing required fields. Keys: {email_data.keys()}")
                return {
                    'error': 'missing_fields',
                    'message': 'Email response missing subject or body',
                    'subject': email_data.get('subject', 'Status Update'),
                    'body': email_data.get('body', content)
                }
            
            # Add metadata
            email_data['metadata'] = {
                'tone': tone,
                'word_count': len(email_data['body'].split()),
                'recipients_count': len(recipients) if recipients else 0
            }
            
            logger.info(f"Email composed successfully: {email_data['subject'][:50]}")
            return email_data
            
        except Exception as e:
            logger.error(f"Email composition failed: {str(e)}", exc_info=True)
            return {
                'error': 'composition_failed',
                'message': f"Failed to compose email: {str(e)}",
                'subject': f'Update: {purpose}',
                'body': f"Email composition encountered an error. Key points:\n\n{key_points_text}"
            }