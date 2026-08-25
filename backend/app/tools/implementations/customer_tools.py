"""Phase 5 - Tools: get_customer_metrics, get_winback_candidates."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.analytics import customers_metrics
from app.services.tool_analytics import winback_candidates_list
from app.tools.base import error_result, success_result
from app.tools.schemas import CustomerMetricsInput, WinbackCandidatesInput

_agent = EvidenceAgent()

def get_customer_metrics(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Customer health metrics."""
    try:
        CustomerMetricsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_customer_metrics", exc.errors()[0]["msg"])
    data = customers_metrics(db)
    evidence = [_agent.build_insight("customer_metrics", data["total_customers"], [
        {"source": "analytics.customers", "metric": "active_customers", "value": data["active_customers"]},
        {"source": "analytics.customers", "metric": "inactive_customers", "value": data["inactive_customers"]},
        {"source": "analytics.customers", "metric": "high_value_customers", "value": data["high_value_customers"]},
        {"source": "analytics.customers", "metric": "win_back_signals", "value": data["win_back_signals"]},
    ])]
    return success_result("get_customer_metrics", data, evidence)

def get_winback_candidates(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Customers inactive beyond threshold, ranked by lifetime spend."""
    try:
        params = WinbackCandidatesInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_winback_candidates", exc.errors()[0]["msg"])
    data = winback_candidates_list(db, params.min_days_inactive, params.limit)
    evidence = [_agent.build_insight("winback_candidates", data["count"], [
        {"source": "analytics.customers", "metric": "winback_count", "value": data["count"]},
        {"source": "analytics.customers", "metric": "total_spend_at_risk", "value": data["total_spend_at_risk"]},
    ])]
    return success_result("get_winback_candidates", data, evidence)
