from typing import Any

from fastapi import APIRouter, Depends

from app.agents.evidence_agent import EvidenceAgent
from app.api.deps import DbSession, get_current_user
from app.models.user import User
from app.services import analytics

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])

agent = EvidenceAgent()


@router.get("/revenue")
def revenue_evidence(
    db: DbSession,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    revenue = analytics.revenue_metrics(db)
    return agent.analyze_revenue(revenue)
