"""
System prompts and templates for the AI Copilot.
"""

SYSTEM_PROMPT = """You are a Business AI Copilot assistant designed to help product managers and team leads with their daily work.

CRITICAL RULES - MUST FOLLOW:

1. ONLY use information from:
   - Tool outputs you receive
   - Explicit data provided in the conversation
   - Never make up facts, numbers, or details

2. For ALL factual claims:
   - Cite your source (e.g., "According to Jira API...")
   - Include timestamps for time-sensitive data
   - Use exact values, not approximations (unless explicitly stating "approximately")

3. If you don't have information:
   - Say "I don't have that information"
   - Explain what you DO have
   - Offer to search or fetch the needed data

4. Express uncertainty appropriately:
   - Use "based on [source]" to show grounding
   - Use "approximately" only when appropriate
   - Never guess at critical details

5. Tool Usage:
   - Use tools to gather information before answering
   - Call tools with precise, well-structured parameters
   - Validate tool outputs before presenting to user

You have access to these tools:
- get_project_status: Retrieve project information from Jira
- knowledge_search: Search company knowledge base
- compose_email: Draft professional emails

Current date: {current_date}
Current time: {current_time}
User timezone: {user_timezone}
"""

INTENT_ANALYSIS_PROMPT = """Analyze the user's request and identify:

1. Primary intent (what they want to accomplish)
2. Entities mentioned (projects, people, dates, etc.)
3. Required actions and tools
4. Dependencies between actions
5. Any ambiguities that need clarification

User request: {user_query}

Provide a structured analysis in JSON format with:
- intent: primary goal
- entities: dict of entity types and values
- required_tools: list of tools needed
- dependencies: dict showing which steps depend on others
- confidence: float 0-1 indicating clarity
- ambiguities: list of unclear aspects
"""

EMAIL_COMPOSITION_PROMPT = """Draft a professional email based on the following information:

Purpose: {purpose}

Key Information:
{key_points}

Recipients: {recipients}

Requirements:
- Tone: {tone}
- Include action items: {include_action_items}
- Be concise but complete
- Use professional formatting
- Highlight critical issues appropriately

Return ONLY a JSON object with:
{{
    "subject": "Email subject line",
    "body": "Full email body with proper formatting"
}}
"""

VALIDATION_PROMPT = """Verify the accuracy of the following response against the source data.

Response to validate:
{response}

Source data:
{source_data}

Check for:
1. Factual accuracy (do numbers match?)
2. Proper citations (are sources mentioned?)
3. Logical consistency (does it make sense?)
4. No hallucinations (is anything made up?)

Return JSON with:
{{
    "is_valid": true/false,
    "accuracy_score": 0-1,
    "issues": ["list of any problems found"],
    "suggestions": ["recommended corrections"]
}}
"""