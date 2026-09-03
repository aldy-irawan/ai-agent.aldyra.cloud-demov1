# AI Infrastructure Agent

AI-powered infrastructure monitoring and investigation system.

## Technologies

- Python
- FastAPI
- Zabbix
- Gemini
- AWS

## Architecture

The system connects infrastructure monitoring with an AI agent for automated investigation and human-approved infrastructure actions.

```text
Browser
   |
   v
FastAPI
   |
   v
AI Agent
   |
   +----> Zabbix API
   |
   +----> Gemini
   |
   v
Investigation
   |
   v
Action Recommendation
   |
   v
Action Manager
   |
   v
Human Confirmation
   |
   v
AWS EC2
```
## Documentation

This project is documented and maintained using Git.

## Project Status

Current implementation includes:

- Zabbix infrastructure monitoring
- AI-powered investigation
- Investigation history
- AI action recommendation
- Human-approved AWS EC2 actions

## Git Workflow

This project uses Git for version control.

Main workflow:

- Create a feature branch
- Make changes
- Review changes with git diff
- Commit changes
- Push branch to GitHub
- Create a Pull Request
- Merge into main
