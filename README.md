# AI Infrastructure Agent

AI-powered infrastructure monitoring and investigation system.

## Technologies

- Python
- FastAPI
- Zabbix
- Gemini
- AWS

## Key Features

- Zabbix infrastructure monitoring
- AI-powered infrastructure investigation
- Investigation history
- AI action recommendation
- Human-approved AWS EC2 actions

## Architecture

```text
Browser
  ↓
FastAPI
  ↓
AI Agent
  ├── Zabbix API
  └── Gemini
  ↓
Investigation
  ↓
Action Recommendation
  ↓
Action Manager
  ↓
Human Confirmation
  ↓
AWS EC2
```

## Project Status

Current implementation includes:

- Zabbix infrastructure monitoring
- Automatic AI investigation
- Investigation history
- AI action recommendation
- Human-approved AWS EC2 STOP action

## Repository Structure

```text
ai-agent/
├── api.py
├── agent_gemini.py
├── zabbix_tools.py
├── action_manager.py
├── investigation_store.py
├── agent.py
├── ai_test.py
├── gemini_test.py
├── test_tools.py
├── zabbix_test.py
├── api_action_ui.py
└── docs/
    └── development-history.md
```

## Documentation

Detailed development history and technical notes:

- [`docs/development-history.md`](docs/development-history.md)

## Roadmap

- Improve AI investigation capabilities
- Expand infrastructure actions
- Improve observability
- Explore MCP integration as a separate project
