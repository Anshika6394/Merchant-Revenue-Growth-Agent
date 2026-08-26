# RevPilot AI — Merchant Revenue & Growth Agent

> **DEMO · SYNTHETIC DATA · SIMULATION** — No real payment actions are executed.

---

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

---

## Architecture

```
SYNTHETIC DATA (SQLite)
        ↓
ANALYTICS ENGINE (Revenue, Payments, Checkout, Customers, Subscriptions, Refunds)
        ↓
OPPORTUNITY DETECTION (6 types: Payment, Checkout, Winback, Subscription, Leakage, Product)
        ↓
AI TOOL LAYER (12 controlled tools — no direct DB access)
        ↓
SPECIALIZED AGENTS (6 agents — evidence-backed recommendations)
        ↓
STRATEGY ORCHESTRATOR (intent-aware, ranked, deduplicated)
        ↓
RAG / MEMORY (TF-IDF vector store, 8 historical business cases)
        ↓
ACTION SIMULATION (5 campaign types, feedback loop)
        ↓
REACT DASHBOARD (8 pages, JWT auth, real API data)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Database | SQLite (dev), synthetic seeded data |
| AI | Anthropic Claude, RAG with TF-IDF |
| Auth | JWT Bearer tokens |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Tests | pytest — 116 tests passing |

---

## Quick Start

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set JWT_SECRET_KEY
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Default Login
```
Email: admin@revpilot.ai
Password: secret
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/v1/auth/login | Login |
| POST | /api/v1/auth/register | Register |
| GET | /api/v1/auth/me | Current user |
| GET | /api/v1/analytics/overview | Revenue overview |
| GET | /api/v1/analytics/payments | Payment metrics |
| GET | /api/v1/analytics/checkout | Checkout metrics |
| GET | /api/v1/analytics/customers | Customer metrics |
| GET | /api/v1/analytics/subscriptions | Subscription metrics |
| GET | /api/v1/analytics/refunds | Refund metrics |
| GET | /api/v1/opportunities | List opportunities |
| POST | /api/v1/opportunities/detect | Run detection |
| POST | /api/v1/agent/strategy | AI strategy query |
| POST | /api/v1/rag/retrieve | RAG retrieval |
| POST | /api/v1/rag/retrieve-grounded | Evidence-grounded RAG |
| POST | /api/v1/actions/simulate | Simulate action |
| GET | /api/v1/actions/ | List actions |
| POST | /api/v1/actions/{id}/feedback | Submit feedback |

---

## Demo Flow (2-3 minutes)

1. **Open dashboard** → Login with default credentials
2. **Overview page** → See gross revenue, failed payment value, abandonment rate
3. **Opportunities page** → Click "Run Detection" → See ranked opportunities
4. **AI Strategy page** → Ask: *"What should I focus on today?"*
5. **View response** → Executive summary + top 3 opportunities + next steps
6. **Simulate action** → POST /api/v1/actions/simulate → See expected ROI
7. **Submit feedback** → Close the feedback loop

---

## Test Results

```
116 passed, 1 warning in 8.79s
9 test files — all phases covered
Phase 1:  Auth & Foundation
Phase 2:  Merchant Data  
Phase 3:  Analytics
Phase 4:  Opportunity Detection
Phase 5:  AI Tool Layer
Phase 6:  Specialized Agents
Phase 7:  Strategy Orchestrator
Phase 8:  RAG & Business Memory
Phase 9:  React Dashboard
Phase 10: Action Simulator
Phase 11: Hardening & Security
```

---

## Key Engineering Decisions

- **No hallucinated numbers** — all financial figures come from DB analytics
- **No real payment actions** — every action is a simulation
- **Modular agent architecture** — each agent is independently testable
- **RAG without external infra** — lightweight TF-IDF, no vector DB needed
- **JWT auth on all endpoints** — no unauthenticated access to data

---

## Important Notes

- All data is **synthetic** and **deterministic** (fixed random seed)
- All financial numbers originate from **database analytics** — never fabricated by AI
- All actions are **simulations** — no real payments executed
- Clearly labeled: **DEMO / SYNTHETIC DATA / SIMULATION**
