# Installation Guide

This document describes the server requirements, dependencies, installation steps, configuration, and verification for **AI Infrastructure Agent**.

> This guide reflects the current project deployment environment. Zabbix Server and Nginx are external prerequisites rather than Python dependencies.

## 1. Server Requirements

| Component | Current Reference |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| CPU | 2 vCPU |
| RAM | ~2 GB |
| Disk | ~29 GB |
| Python | 3.12.3 |
| pip | 24.0 |
| Git | 2.43.0 |
| AWS CLI | 2.36.34 |
| jq | 1.7 |
| Nginx | 1.24.0 |
| systemd | Required |
| Zabbix Server | Required |

Higher resources may be appropriate for production workloads.

## 2. System Dependencies

Required system components:

- Python 3
- Python virtual environment (`venv`)
- Git
- AWS CLI
- `jq`
- Nginx
- systemd
- Zabbix Server/API access

Ubuntu packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git jq nginx
```

Verify:

```bash
python3 --version
pip3 --version
git --version
aws --version
jq --version
nginx -v
```

## 3. Project Setup

Clone the repository:

```bash
git clone https://github.com/aldy-irawan/ai-agent.aldyra.cloud-demov1.git
cd ai-agent.aldyra.cloud-demov1
```

Current deployment directory:

```text
/home/ubuntu/ai-agent
```

## 4. Python Virtual Environment

Create the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify:

```bash
which python
python --version
```

Expected path:

```text
/home/ubuntu/ai-agent/.venv/bin/python
```

## 5. Python Packages

Install application dependencies:

```bash
pip install -r requirements.txt
```

Current `requirements.txt`:

```text
fastapi==0.141.1
pydantic==2.46.4
python-dotenv==1.2.3
google-genai==2.20.0
requests==2.34.2
uvicorn==0.52.4
```

Python standard-library modules such as `os`, `json`, `sqlite3`, `subprocess`, `uuid`, and `datetime` do not require pip installation.

`ai_test.py` currently imports the OpenAI package. It is an optional/testing script and is not part of the main Gemini runtime dependency list.

## 6. Environment Configuration

The application uses:

```text
.env
```

Never commit the real `.env`.

Create it from the example:

```bash
cp .env.example .env
nano .env
```

Example configuration:

```env
ZABBIX_URL=https://your-zabbix-server.example.com/api_jsonrpc.php
ZABBIX_API_TOKEN=your_zabbix_api_token_here

GEMINI_API_KEY=your_gemini_api_key_here

ZABBIX_WEBHOOK_TOKEN=your_webhook_token_here

AWS_REGION=ap-southeast-1
AWS_ACTION_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/AI-Infrastructure-Action-Role
```

Use real values only on the server.

## 7. Zabbix Configuration

The AI Agent communicates with Zabbix through the Zabbix API and requires a valid API token with appropriate permissions.

The application exposes:

```text
POST /zabbix-webhook
```

Incoming webhook requests are authenticated using `ZABBIX_WEBHOOK_TOKEN`.

The current Zabbix Action is:

```text
Automatic Infrastructure Investigation
```

with trigger severity:

```text
Warning and higher
```

Matching Zabbix trigger events can therefore be sent automatically to the AI investigation endpoint.

## 8. AWS Configuration

AWS functionality is used for infrastructure monitoring and the controlled EC2 action workflow.

Current demo region:

```text
ap-southeast-1
```

State-changing actions use a dedicated IAM role:

```text
AI-Infrastructure-Action-Role
```

The monitoring role and action role are intentionally separated.

### Safety Model

The AI does not directly execute destructive AWS actions:

```text
AI Investigation
       ↓
AI Action Recommendation
       ↓
Action Manager Proposal
       ↓
Human Confirmation
       ↓
AWS Action
```

The current controlled EC2 action is:

```text
STOP
```

The action role should follow least privilege.

## 9. EC2 Action Script

The script is stored in:

```text
scripts/ai_ec2_action.sh
```

Make it executable:

```bash
chmod +x scripts/ai_ec2_action.sh
```

Supported actions:

```text
check
stop
```

The script validates the action, finds the EC2 instance by `Name` tag, verifies the target, retrieves instance information, and for STOP verifies that the instance is running before assuming the dedicated Action Role and calling `StopInstances`.

The repository version must contain only a placeholder account ID:

```text
arn:aws:iam::YOUR_ACCOUNT_ID:role/AI-Infrastructure-Action-Role
```

Never commit AWS credentials or tokens.

## 10. systemd Service

The AI Agent runs as:

```text
ai-agent.service
```

Service file:

```text
/etc/systemd/system/ai-agent.service
```

Current deployment uses:

```text
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/ai-agent
EnvironmentFile=/home/ubuntu/ai-agent/.env
```

Uvicorn is started from the project virtual environment:

```text
/home/ubuntu/ai-agent/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
```

After creating or changing the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent.service
sudo systemctl start ai-agent.service
```

Check:

```bash
sudo systemctl status ai-agent.service
systemctl is-enabled ai-agent.service
```

Expected:

```text
enabled
```

Logs:

```bash
sudo journalctl -u ai-agent.service -f
```

## 11. Nginx

Nginx is used as the web server/reverse proxy.

Current site configuration:

```text
/etc/nginx/sites-available/ai-agent
```

Enabled through:

```text
/etc/nginx/sites-enabled/ai-agent
```

The enabled file is a symbolic link to the site configuration.

Test configuration:

```bash
sudo nginx -t
```

Reload:

```bash
sudo systemctl reload nginx
```

Check:

```bash
sudo systemctl status nginx
```

The exact server block is environment-specific.

## 12. Application Verification

Check the FastAPI health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Check the service:

```bash
systemctl status ai-agent.service
```

Check port 8000:

```bash
ss -lntp | grep 8000
```

Verify the virtual environment:

```bash
source .venv/bin/activate
which python
pip list
```

## 13. Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/health` | Health check |
| POST | `/analyze` | AI infrastructure analysis |
| POST | `/ask` | Ask the AI Agent |
| GET | `/investigations` | Investigation history |
| POST | `/zabbix-webhook` | Receive Zabbix events |

Action Manager also provides routes for the human-confirmed action workflow.

## 14. Recommended Functional Test

1. Verify `.env`.
2. Verify Zabbix API connectivity.
3. Verify Gemini configuration.
4. Start `ai-agent.service`.
5. Check `/health`.
6. Open the web UI.
7. Test an AI investigation.
8. Test the Zabbix webhook.
9. Verify Investigation History.
10. Test AWS action only in the designated demo environment.
11. Confirm human approval before any state-changing action.

## 15. Optional Testing Scripts

Development/testing scripts include:

```text
agent.py
ai_test.py
gemini_test.py
test_tools.py
zabbix_test.py
```

These are useful for development and troubleshooting but are not all required for production runtime.

## 16. Repository Structure

```text
ai-agent.aldyra.cloud/
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   ├── development-history.md
│   └── installation.md
├── action_manager.py
├── agent.py
├── agent_gemini.py
├── ai_test.py
├── api.py
├── api_action_ui.py
├── gemini_test.py
├── investigation_store.py
├── test_tools.py
├── zabbix_test.py
├── zabbix_tools.py
└── scripts/
    └── ai_ec2_action.sh
```

Runtime files and secrets such as `.env` and the SQLite investigation database are intentionally excluded from Git.

## 17. Security Notes

Never commit:

- `.env`
- API tokens
- Gemini API keys
- AWS access keys
- AWS secret keys
- webhook tokens
- real account credentials
- sensitive runtime databases

The repository should contain placeholders only.

For AWS actions, maintain separation between the Monitoring Role and Action Role. The Action Manager must remain behind explicit human confirmation for state-changing operations.

## 18. Current Reference Deployment

```text
Ubuntu 24.04.4 LTS
        │
        ├── Zabbix Server
        │
        ├── Nginx
        │
        └── AI Infrastructure Agent
                │
                ├── FastAPI / Uvicorn
                ├── Gemini
                ├── Zabbix API
                ├── Investigation History
                └── Action Manager
                        │
                        └── AWS EC2
```

Project directory:

```text
/home/ubuntu/ai-agent
```

FastAPI/Uvicorn:

```text
0.0.0.0:8000
```

Public access is handled through Nginx and the configured domain.

## 19. Maintenance

When Python dependencies change:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

After application code changes:

```bash
sudo systemctl restart ai-agent.service
curl http://127.0.0.1:8000/health
```

After Nginx configuration changes:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Document Status

This document describes the current reference deployment of **AI Infrastructure Agent** and should be updated when the architecture, dependencies, deployment process, or security model changes.
