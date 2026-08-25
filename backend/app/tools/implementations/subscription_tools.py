"""Phase 5 - Tool: get_subscription_risks."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.analytics import subscriptions_metrics
from app.services.tool_analytics import subscription_risks_list
from app.tools.base import error_result, success_result
from app.tools.schemas import SubscriptionRisksInput

_agent = EvidenceAgent()

def get_subscription_risks(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Subscriptions at risk of churning."""
    try:
        params = SubscriptionRisksInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_subscription_risks", exc.errors()[0]["msg"])
    data = subscription_risks_list(db, params.risk_level, params.limit)
    agg = subscriptions_metrics(db)
    data["global_stats"] = agg
    evidence = [_agent.build_insight("subscription_risks", data["count"], [
        {"source": "analytics.subscriptions", "metric": "at_risk_count", "value": data["count"]},
        {"source": "analytics.subscriptions", "metric": "total_at_risk_mrr", "value": data["total_at_risk_mrr"]},
        {"source": "analytics.subscriptions", "metric": "retention_risk", "value": agg.get("retention_risk", 0)},
    ])]
    return success_result("get_subscription_risks", data, evidence)
