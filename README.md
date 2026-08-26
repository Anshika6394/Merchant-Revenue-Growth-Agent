# RevPilot AI — Merchant Revenue & Growth Agent

> **DEMO · SYNTHETIC DATA · SIMULATION** — No real payment actions are executed.

## Problem

Merchants lose revenue every day due to:
- Payment failures and declines
- Checkout abandonment
- Customer churn and inactivity
- Subscription payment failures
- Refund leakage
- Low product conversion

## Solution

RevPilot AI continuously analyzes merchant intelligence and identifies **evidence-backed revenue opportunities** with specific, actionable recommendations.

## Architecture

```
DATA (Synthetic SQLite)
  → ANALYTICS (Revenue, Payments, Checkout, Customers, Subscriptions, Refunds)
  → OPPORTUNITY DETECTION (6 opportunity types with scoring)
  → AI TOOL LAYER (12 controlled tools, no direct DB access)
  → SPECIALIZED AGENTS (6 agents: Payment, Checkout, Winback, Subscription, Leakage, Product)
  → STRATEGY ORCHESTRATOR (intent-aware, ranked, deduplicated)
  → RAG / MEMORY (TF-IDF vector store, 8 historical business cases)
  → ACTION SIMULATION (5 campaign types, feedback loop)
  → DASHBOARD (React/TypeScript, 8 pages)
```

## Core Capabilities

| Capability | Description |
|---|---|
| Payment Recovery | Detect retry-eligible failed payments |
| Checkout Recovery | Identify abandoned cart opportunities |
| Customer Win-back | Find high-value inactive customers |
| Subscription Retention | Detect at-risk subscriptions |
| Refund Leakage | Spot unusual refund concentration |
| Product Growth | Find high-converting low-visibility products |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, SQLite
- **AI**: Claude (Anthropic), RAG with TF-IDF vector store
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Auth**: JWT bearer tokens
- **Tests**: pytest, 116 tests passing

## Quick Start

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/analytics/overview | Revenue overview |
| GET | /api/v1/opportunities | List opportunities |
| POST | /api/v1/opportunities/detect | Run detection |
| POST | /api/v1/agent/strategy | AI strategy query |
| POST | /api/v1/rag/retrieve | RAG retrieval |
| POST | /api/v1/actions/simulate | Simulate action |
| POST | /api/v1/actions/{id}/feedback | Submit feedback |

## Demo Flow

1. Open dashboard → Login
2. View revenue overview and opportunities
3. Click an opportunity → See evidence
4. Go to AI Strategy → Ask: "What should I focus on today?"
5. View ranked recommendations with impact estimates
6. Simulate an action → See expected ROI
7. Submit feedback → Close the loop

## Test Results

```
116 passed in 8.33s
9 test files covering all phases
```

## Important Notes

- All data is **synthetic** and **deterministic** (seeded)
- All financial numbers originate from **database analytics** — never fabricated
- All actions are **simulations** — no real payments executed
- JWT authentication required for all API endpoints
