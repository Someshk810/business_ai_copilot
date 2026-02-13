# Quick Start Guide

## 1. Setup (5 minutes)
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Required
JIRA_URL=https://your-company.atlassian.net  # Optional
JIRA_EMAIL=you@company.com  # Optional
JIRA_API_TOKEN=your_token  # Optional
```

## 2. Run Example (1 minute)
```bash
python example.py
```

## 3. Try Interactive Mode
```bash
python -m src.main
```

Try these queries:
- "Get Phoenix status and draft email"
- "Search for team documentation"
- "Draft a status update email"

## 4. Without Jira (Demo Mode)

The copilot works without Jira using:
- Mock project data
- Sample knowledge base
- Full email composition

Perfect for testing!

## Next Steps

- Add your company documents to vector database
- Connect to your Jira instance
- Customize prompts in `config/prompts.py`
- Add new tools in `src/tools/`