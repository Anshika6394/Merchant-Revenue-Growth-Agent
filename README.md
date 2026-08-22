# RevPilot AI

Evidence-driven, simulated merchant revenue intelligence for the Razorpay AI Buildathon 2026. It uses synthetic data only and never executes real payment actions.

## Phase 1

The backend foundation includes FastAPI, SQLAlchemy, Alembic, JWT authentication, Docker Compose, configuration, and API tests. Future phases will add data, analytics, evidence-bound agents, retrieval, simulations, and the React dashboard.

## Architecture

`app/api` owns HTTP routes; `models` persistence; `schemas` validation; `repositories` database access; `services` business logic. Future `agents` and `tools` will host the evidence-driven workflow.

## Local run

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Set `POSTGRES_PASSWORD` and `JWT_SECRET_KEY` in your environment before running `docker compose up --build`. Health: `GET /health`; docs: `/docs`.
