# AI Infrastructure Agent — Development History

This document contains the detailed development history and technical notes for the
`ai-agent.aldyra.cloud` project.

The root `README.md` is intentionally kept concise. This file preserves the deeper
context so the project can be revisited later without losing the development journey.

AI-powered infrastructure monitoring, investigation, correlation, and controlled operations system.

Project ini menghubungkan **Zabbix**, **AI Agent**, **Gemini**, **FastAPI**, dan **AWS** untuk membantu proses monitoring dan investigation infrastructure, dengan prinsip bahwa **state-changing action tetap membutuhkan human approval**.

---

## Technologies

- Python
- FastAPI
- Zabbix
- Gemini
- AWS

---

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
   |------> Zabbix API
   |
   +------> Gemini
   |
   v
Investigation
   |
   v
Correlation
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

### Operational Flow

```text
MONITOR
   |
   v
INVESTIGATE
   |
   v
CORRELATE
   |
   v
EXPLAIN
   |
   v
RECOMMEND
   |
   v
PROPOSE
   |
   v
HUMAN APPROVE
   |
   v
ACT
   |
   v
VERIFY
   |
   v
AUDIT / HISTORY
```

---

## Main Components

### `api.py`

Web/API layer yang menjadi interface antara browser, AI Agent, Zabbix webhook, dan Action Manager.

Main endpoints:

```text
GET  /
GET  /health
GET  /analyze
POST /ask
GET  /investigations
POST /zabbix-webhook

POST /action/propose
POST /action/confirm
```

Responsibilities:

- Infrastructure Monitoring Dashboard
- AI Analysis
- Ask AI
- Investigation History
- Zabbix Webhook
- AI Action Proposal
- Human Confirmation
- Controlled EC2 action execution

---

### `zabbix_tools.py`

Tool layer yang digunakan AI Agent untuk berkomunikasi dengan Zabbix.

Responsibilities include:

- Retrieve active problems
- Retrieve CPU utilization
- Retrieve memory utilization
- Retrieve hosts
- Collect infrastructure monitoring data
- Provide monitoring data for AI investigation

Zabbix digunakan sebagai source of monitoring data untuk investigation.

---

### `agent_gemini.py`

Core AI Agent dan Gemini integration.

Responsibilities:

- Collect Zabbix data
- Analyze infrastructure condition
- Investigate active problems
- Perform multi-host analysis
- Correlate problems with resource utilization
- Generate explanations
- Generate recommended next steps
- Generate structured action recommendations

AI tidak langsung melakukan state-changing action.

---

### `investigation_store.py`

Storage layer untuk Investigation History.

Responsibilities:

- Store investigation results
- Track investigation lifecycle
- Store Zabbix event information
- Prevent duplicate investigations
- Provide investigation history to the UI

Runtime database digunakan untuk history dan tidak disimpan ke Git repository.

---

### `action_manager.py`

Control layer untuk infrastructure action.

Architecture:

```text
AI Recommendation
       |
       v
Action Manager
       |
       v
Safety Decision
       |
       v
Human Confirmation
       |
       v
AWS Action
       |
       v
Verification
```

Action Manager memisahkan **AI reasoning** dari **state-changing execution**.

---

## Automatic Investigation

Zabbix dapat mengirim event ke AI Agent melalui webhook.

```text
Zabbix Trigger
      |
      v
Zabbix Action
      |
      v
Webhook
      |
      v
FastAPI /zabbix-webhook
      |
      v
AI Investigation
      |
      v
Investigation History
```

Current Zabbix Action digunakan untuk trigger severity:

```text
Warning and higher
```

Artinya event yang memenuhi kondisi tersebut dapat dikirim ke AI Agent untuk automatic investigation.

---

## Investigation & Correlation

AI Agent tidak hanya melihat satu problem secara terisolasi.

Investigation dapat mencakup:

- Multi-host investigation
- Problem correlation
- CPU correlation
- Memory correlation
- Intra-host correlation
- Cross-host correlation
- Severity prioritization
- Comparative assessment
- Fact vs hypothesis separation
- Likely explanation
- Recommended next steps

Contoh konsep:

```text
Host A
  CPU High
  |
  +----+
       |
       v
   Correlation
       ^
       |
  Host B
  Memory High
```

Tujuannya adalah membantu membedakan antara **single-host problem** dan kemungkinan **infrastructure-wide issue**.

---

## Investigation History

Setiap automatic investigation dapat disimpan ke history.

History menyimpan informasi seperti:

- Investigation ID
- Timestamp
- Zabbix event
- Host
- Severity
- Problem
- Status
- Duration
- Investigation details

UI menggunakan konsep:

```text
VIEW
  |
  v
Investigation Details
  |
  v
HIDE
```

Duplicate protection digunakan agar event yang sama tidak diproses berulang sebagai investigation baru.

---

## AI Action Recommendation

AI dapat memberikan recommendation ketika hasil investigation menunjukkan bahwa infrastructure action mungkin diperlukan.

Contoh konsep:

```text
Investigation
      |
      v
AI Recommendation
      |
      +----> NO ACTION
      |
      +----> REVIEW ACTION
```

AI recommendation bersifat **advisory**.

AI tidak diberikan hak untuk langsung menjalankan destructive/state-changing action.

---

## Human-Approved AWS Actions

Untuk state-changing action, project menggunakan human-in-the-loop model.

```text
AI Recommendation
       |
       v
Action Proposal
       |
       v
Human Review
       |
       +---- NO
       |
       +---- YES
              |
              v
        AWS Execution
              |
              v
          Verification
```

### EC2 STOP

EC2 STOP telah berhasil diuji end-to-end:

```text
AI Recommendation
       |
       v
Action Manager Proposal
       |
       v
Human Confirmation
       |
       v
AWS StopInstances
       |
       v
Verify Instance State
       |
       v
STOPPED
```

Safety behavior juga diuji.

Jika instance sudah dalam kondisi `STOPPED`, request STOP kembali akan ditolak sebagai action yang tidak aman/tidak diperlukan.

### EC2 START

EC2 START belum diaktifkan pada Action Manager saat dokumentasi ini dibuat.

---

## Safety Model

Project menggunakan tiga level konsep:

### Level 1 — AI Recommendation

AI hanya menganalisis dan memberikan recommendation.

```text
AI
 |
 +--> Recommendation
```

### Level 2 — Controlled Action

AI membuat proposal, tetapi human harus melakukan explicit confirmation.

```text
AI
 |
 v
Proposal
 |
 v
Human Approval
 |
 v
Execution
```

**Status: IMPLEMENTED**

### Level 3 — Autonomous Action

AI menjalankan state-changing action tanpa human approval.

**Status: NOT IMPLEMENTED**

Prinsip utama:

- AI tidak boleh mengarang kondisi infrastructure.
- Investigation menggunakan data monitoring dari Zabbix.
- State-changing action membutuhkan human approval.
- AWS action menggunakan dedicated IAM action role.
- Final state selalu diverifikasi.
- Destructive/autonomous action tidak digunakan secara default.

---

## Project Status

Current implementation includes:

- [x] Zabbix infrastructure monitoring
- [x] AI-powered investigation
- [x] Multi-host investigation
- [x] Investigation history
- [x] Duplicate protection
- [x] AI correlation
- [x] AI action recommendation
- [x] Action Manager
- [x] Human approval
- [x] AWS EC2 STOP
- [x] Final-state verification
- [ ] AWS EC2 START
- [ ] More controlled AWS actions
- [ ] Advanced action governance
- [ ] Controlled automation for selected low-risk actions

---

## Development Milestones

### Phase 1 — Foundation

1. Python environment
2. Zabbix API connectivity
3. Zabbix problem retrieval
4. CPU and memory retrieval
5. Gemini integration

### Phase 2 — AI Agent

6. AI Agent implementation
7. Zabbix data collection
8. AI infrastructure analysis
9. Simple and detailed output modes

### Phase 3 — Web Application

10. FastAPI API layer
11. Infrastructure monitoring dashboard
12. Ask AI
13. AI output formatting
14. systemd service

### Phase 4 — Automated Investigation

15. Zabbix webhook
16. Automatic investigation
17. Investigation History
18. Duplicate protection

### Phase 5 — AI Intelligence

19. Multi-host investigation
20. Correlation analysis
21. Comparative assessment
22. Severity prioritization
23. Fact vs hypothesis separation

### Phase 6 — Controlled Operations

24. AI action recommendation
25. Action Manager
26. Safety decision
27. Human confirmation
28. AWS EC2 STOP
29. Final-state verification

---

## Development Lessons

Several engineering problems were encountered and resolved during development.

### Gemini Quota

Gemini Free Tier returned:

```text
429 RESOURCE_EXHAUSTED
```

Root cause was excessive model invocation during tool-calling experiments.

The architecture was refactored so that Zabbix data is collected first and Gemini performs analysis with a more controlled request flow.

### Gemini Availability

Transient errors such as:

```text
503 UNAVAILABLE
```

showed that external AI dependencies must be treated as unreliable dependencies.

### API / Agent Interface

Parameter mismatches between FastAPI and the AI Agent caused runtime errors.

Lesson:

```text
API contract
    =
clear input/output interface
```

### Frontend Rendering

Raw AI output and object rendering caused UI issues such as:

```text
[object Object]
```

The UI was revised to render structured AI results and Markdown more cleanly.

### Infrastructure Action Safety

A major design decision was made:

```text
AI should reason,
Action Manager should control,
Human should approve,
AWS should execute,
System should verify.
```

## Zabbix MCP

Zabbix MCP is treated as a **separate project/workstream** from `ai-agent.aldyra.cloud`.

Conceptually:

```text
Custom AI Agent
      |
      +----> zabbix_tools.py ----> Zabbix
      |
      +----> aws tools ----------> AWS
```

versus:

```text
AI Client
    |
    v
   MCP
    |
    +----> Zabbix MCP ----> Zabbix
    |
    +----> AWS MCP -------> AWS
```

The current project focuses on the custom AI Agent architecture, while Zabbix MCP is developed separately.

---

## Roadmap

### Next

- Improve AI action recommendation
- Add more controlled AWS actions
- Improve action audit trail
- Add stronger policy and safety controls
- Improve documentation
- Add automated tests
- Improve deployment and configuration documentation

### Future

Potential controlled automation:

```text
Monitoring
    ↓
Investigation
    ↓
Recommendation
    ↓
Policy Evaluation
    ↓
Approval
    ↓
Action
    ↓
Verification
    ↓
Audit
```

Autonomous state-changing operations should only be considered for carefully selected low-risk actions after sufficient governance and safety controls are established.

---

## Final Project Position

The project has evolved from a simple monitoring assistant into a controlled AI infrastructure operations platform:

```text
AI Infrastructure Monitoring
        +
Investigation
        +
Correlation
        +
Recommendation
        +
Controlled Operations
```

Long-term target:

```text
MONITOR
   ↓
INVESTIGATE
   ↓
CORRELATE
   ↓
EXPLAIN
   ↓
RECOMMEND
   ↓
PROPOSE
   ↓
HUMAN APPROVE
   ↓
ACT
   ↓
VERIFY
   ↓
AUDIT
```

---

## Project

**Project:** `ai-agent.aldyra.cloud`

**GitHub Repository:** `ai-agent.aldyra.cloud-demov1`

This repository documents the engineering journey of building an AI-assisted infrastructure monitoring and controlled operations system.
