# Business AI Copilot

An intelligent assistant for product managers and team leads, built with LangGraph and Claude.

## Features

- 🎯 **Project Status Retrieval**: Get real-time project status from Jira
- 📚 **Knowledge Search**: Semantic search over company documentation
- ✉️ **Email Composition**: AI-powered professional email drafting
- 🔄 **Multi-Step Workflows**: Orchestrated task execution with LangGraph
- ✅ **Validation & Safety**: Factual verification and hallucination prevention

## Prerequisites

- Python 3.10+
- Anthropic API key
- (Optional) Jira account and API token

## Quick Start (5 minutes)

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:
- **Windows:** `.\.venv\Scripts\activate`
- **macOS/Linux:** `source .venv/bin/activate`

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required
JIRA_URL=https://your-company.atlassian.net  # Optional
JIRA_EMAIL=you@company.com            # Optional
JIRA_API_TOKEN=your_token             # Optional
LOG_LEVEL=INFO
```

### 4. Run the Application

```bash
python -m src.main
```

## Usage

### Interactive Mode
```bash
python -m src.main
```

Try these queries:
- "Get Phoenix status and draft email"
- "Search for team documentation"
- "Draft a status update email"

### Run Example
```bash
python example.py
```

### Demo Mode (Without Jira)

The copilot works without Jira using mock data and a sample knowledge base—perfect for testing!

## Project Structure

```
business-ai-copilot/
├── config/              # Configuration and prompts
├── src/
│   ├── agent/          # LangGraph orchestration
│   ├── tools/          # Tool implementations
│   ├── integrations/   # External system integrations
│   ├── validation/     # Output validators
│   └── utils/          # Utilities and logging
├── tests/              # Test suite
├── requirements.txt    # Dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Tools Available

### get_project_status
Retrieves project information from Jira including:
- Completion percentage
- Active sprint details
- Task breakdown
- Blocker identification
- Velocity metrics

### knowledge_search
Semantic search over company knowledge base:
- Documentation files
- Team wikis
- Policies and procedures
- Project documentation

### compose_email
AI-powered email composition:
- Professional tone adjustment
- Action item extraction
- Recipient formatting
- Subject line generation

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

1. Create tool class in `src/tools/`
2. Inherit from `Tool` base class
3. Implement `execute()` method
4. Register in orchestrator

### Extending Workflows

Edit `src/agent/orchestrator.py` to:
- Add new nodes
- Define routing logic
- Create conditional paths

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `JIRA_URL`: Your Jira instance URL
- `JIRA_EMAIL`: Jira user email
- `JIRA_API_TOKEN`: Jira API token
- `LOG_LEVEL`: Logging level (default: INFO)

### Customization

Edit `config/prompts.py` to customize:
- System prompts
- Email templates
- Validation rules

## Troubleshooting

### Jira Connection Issues
- Verify `JIRA_URL` is correct (include https://)
- Check API token has proper permissions
- Ensure Jira credentials in `.env` are valid

### Virtual Environment Issues
- Make sure you're in the activated virtual environment
- Run `pip install --upgrade pip` before installing dependencies
- If dependencies conflict, try: `pip install --upgrade -r requirements.txt`

### API Rate Limits
- Implement request throttling for high-volume queries
- Check API rate limit documentation

## Next Steps

- Add your company documents to the vector database
- Connect to your Jira instance
- Customize prompts in `config/prompts.py`
- Add new tools in `src/tools/`
- Extend workflows in `src/agent/`
