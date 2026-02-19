# Business AI Copilot

An intelligent AI-powered assistant that helps teams manage tasks, projects, and communications. The copilot integrates with Jira, email systems, and knowledge bases to provide contextual assistance through a conversational interface.

## Features

- **Task & Project Management**: Fetch project status, create tasks, and manage workflows via Jira integration
- **Smart Email Composition**: Draft professional emails with context awareness
- **Knowledge Search**: Query your company's documentation and knowledge base using vector embeddings
- **Priority Planning**: Intelligently organize and prioritize tasks based on context
- **Calendar Management**: Schedule meetings and manage team calendars
- **Conversational Interface**: Interact through a Gradio web UI or command-line
- **LLM-Powered Reasoning**: Uses Claude and Google's LLMs with chain-of-thought capabilities
- **Works Offline**: Demo mode available without external integrations

## Architecture

```
Business AI Copilot
├── UI Layer (Gradio)
├── Agent System (LangGraph)
│   ├── Orchestrator (State Management)
│   ├── Nodes (Tool Executors)
│   └── State (Context Management)
├── Tools Layer
│   ├── Task Manager (Jira)
│   ├── Email Composer
│   ├── Knowledge Search (Vector DB)
│   ├── Priority Planner
│   ├── Project Status
│   └── Calendar Manager
├── Integrations
│   ├── Jira Client
│   └── ChromaDB Vector Store
└── Config & Validation
    ├── Prompts
    ├── Settings
    └── Validators
```

## Quick Start

### Installation

1. **Clone the repository**
   ```bash
   cd business_ai_copilot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # or
   .\.venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add:
   ```
   GOOGLE_API_KEY=your_google_api_key  # Required 
   DEFAULT_MODEL=gemini-2.5-flash      # Google Gemini model
   JIRA_URL=https://your-company.atlassian.net  # Optional
   JIRA_EMAIL=you@company.com  # Optional
   JIRA_API_TOKEN=your_token  # Optional (get from Jira account settings)
   ```

### Running the Application

**Interactive Web UI:**
```bash
python launch_ui.py
```
Opens a Gradio interface at `http://localhost:7860`

**Command-line Mode:**
```bash
python -m src.main
```

**Example Scripts:**
```bash
python example.py              # Basic example
python example_priority_plan.py # Priority planning example
```

### Demo Mode (No Integrations Required)

The copilot works perfectly without external integrations using mock data and sample knowledge:
```bash
python example.py
```

Try these queries:
- "What's the status of the Phoenix project?"
- "Draft an email summarizing team progress"
- "Search for deployment best practices"
- "Create a priority plan for this week"

## Project Structure

```
src/
├── main.py              # Entry point for CLI mode
├── agent/
│   ├── orchestrator.py  # LangGraph agent orchestration
│   ├── nodes.py         # Tool executor nodes
│   ├── state.py         # Agent state definitions
│   └── __init__.py
├── tools/
│   ├── base.py          # Base tool interface
│   ├── task_manager.py  # Jira integration
│   ├── email_composer.py
│   ├── knowledge_search.py
│   ├── priority_planner.py
│   ├── project_status.py
│   └── calendar_manager.py
├── integrations/
│   ├── jira_client.py   # Jira API wrapper
│   ├── vector_db.py     # ChromaDB integration
│   └── __init__.py
├── ui/
│   └── gradio_app.py    # Web interface
├── utils/
│   ├── helpers.py
│   ├── logging_config.py
│   └── __init__.py
└── validation/
    └── validators.py    # Input validation

config/
├── prompts.py           # LLM system prompts
├── settings.py          # Configuration
└── tests/
    ├── test_tools.py
    └── test_workflow.py

data/
└── chroma_db/           # Vector database storage

logs/                     # Application logs
```

## Configuration

### Prompts (`config/prompts.py`)

Customize LLM behavior by editing system prompts for different tools and agent behaviors.

### Settings (`config/settings.py`)

- LLM model selection (Claude, Google Gemini)
- Vector database configuration
- Jira connection settings
- Tool availability toggles

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
```

### Adding New Tools

1. Create a new file in `src/tools/`
2. Inherit from `BaseTool` in `base.py`
3. Implement `execute()` method
4. Register in agent orchestrator (`src/agent/orchestrator.py`)

Example:
```python
from src.tools.base import BaseTool

class MyNewTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What this tool does"
        )
    
    async def execute(self, **kwargs):
        # Implementation
        return result
```

## Key Technologies

- **LangChain & LangGraph**: Multi-agent orchestration framework
- **Google Gemini**: Primary Large Language Model (gemini-2.5-flash)
- **Jira**: Project management integration
- **ChromaDB**: Vector database for semantic search
- **Gradio**: Web UI framework
- **Pydantic**: Data validation

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `DEFAULT_MODEL` | No | LLM model (default: gemini-2.5-flash) |
| `JIRA_URL` | No | Jira instance URL |
| `JIRA_EMAIL` | No | Jira account email |
| `JIRA_API_TOKEN` | No | Jira API token |

## Troubleshooting

**Import errors:**
```bash
pip install -r requirements.txt --force-reinstall
```

**API authentication failures:**
- Verify `.env` file is in the root directory
- Check API keys are valid and not revoked
- Ensure proper permissions for Jira access

**Jira connection issues:**
- Confirm Jira URL format (include https://)
- Check firewall/VPN connectivity
- Verify API token has necessary scopes

## Contributing

1. Create a feature branch
2. Make changes and test locally
3. Run tests: `pytest`
4. Format code: `black .`
5. Submit pull request
