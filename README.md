# AI DevOps Agent — MVP Demo

Self-contained local demo of the AI DevOps Agent described in
`AI-devops-agent.pdf`: anomaly detection, LLM-based root-cause analysis,
automated remediation suggestions, and a 5-screen dashboard for
human-in-the-loop approval.

## Architecture

```
sample_service (buggy code)
        │
scenarios/code_exception.py   ── injects TypeErrors via HTTP
        │
        ▼
POST /api/ingest  ── detection engine (rule thresholds)
        │
        ▼
Alert  ─►  /api/.../diagnose  ─► OpenAI → Diagnosis
        │                                   │
        │                                   ▼
        └─►  /api/.../remediate  ─► OpenAI → unified diff
                                             │
                                             ▼
                            /api/remediations/:id/approve
                                             │
                                             ▼
                                  writes patch to disk
```

Stack: **FastAPI + SQLite + OpenAI** backend, **React + Vite +
TypeScript** frontend.

## Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

## Setup

```bash
cd ai-devops-agent
cp .env.example .env
# edit .env — set OPENAI_API_KEY

# backend
python -m venv .venv
source .venv/bin/activate
pip install -e .

# frontend
cd frontend
npm install
cd ..
```

## Run the demo

Three terminals:

```bash
# 1) Backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# 2) Frontend
cd frontend && npm run dev
# open http://localhost:5173

# 3) Trigger the failure scenario
source .venv/bin/activate
python -m backend.scenarios.code_exception --count 5
```

Within ~1–2 seconds an alert should appear on the dashboard. Walk
through the 5 screens:

1. **Alert Dashboard** — click the new alert row
2. **Investigation** — see stack trace and event timeline
3. **Diagnosis** — click "Run LLM diagnosis" (calls OpenAI)
4. **Remediation** — click "Generate remediation" (LLM produces diff)
5. **Approval** — click "Approve & apply" — patch is written to
   `sample_service/buggy_service.py`

Verify the fix worked by re-running:

```bash
python -m backend.scenarios.code_exception --count 5
```

The script will report "No exception raised — the bug may already be
fixed!" (or no new alert will appear). The KPI sidebar shows
detection latency, diagnosis latency, and MTTR.

## Project layout

```
backend/           FastAPI app, detection engine, RCA, remediation
  api/             REST routers (alerts, diagnosis, remediation, metrics, stream)
  connectors/      Sentry-style event schema (mock)
  detection/       Rule-based anomaly detector
  rca/             OpenAI-powered root cause analysis
  remediation/     OpenAI-powered patch generator
  scenarios/       Fault injection scripts
sample_service/    Intentionally buggy code used in the demo
frontend/          React + Vite dashboard (5 screens)
```

## Scope / limitations (MVP)

- Simulated Sentry connector only (no real Sentry/Prometheus/CloudWatch)
- Code-exception scenario only (no infra fault / perf spike scenarios)
- Rule-based anomaly detection (no ML)
- Single-user, no auth
- SQLite, wiped by deleting `devops_agent.db`

These were deliberately deferred — see the plan file for details.

## Resetting state

```bash
rm devops_agent.db
# restore the intentional bug so you can re-demo:
git checkout sample_service/buggy_service.py   # or edit manually
```
