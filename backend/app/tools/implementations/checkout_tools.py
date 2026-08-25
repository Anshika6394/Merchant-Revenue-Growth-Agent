"""Phase 5 - Tool: get_checkout_metrics."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.tool_analytics import checkout_for_period
from app.tools.base import error_result, success_result
from app.tools.schemas import CheckoutMetricsInput

_agent = EvidenceAgent()

def get_checkout_metrics(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Checkout funnel metrics - starts, completions, abandonment."""
    try:
        params = CheckoutMetricsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_checkout_metrics", exc.errors()[0]["msg"])
    data = checkout_for_period(db, params.start(), params.end())
    evidence = [_agent.build_insight("checkout_metrics", data["abandonment_rate"], [
        {"source": "analytics.checkout", "metric": "checkout_starts", "value": data["checkout_starts"]},
        {"source": "analytics.checkout", "metric": "completed_checkouts", "value": data["completed_checkouts"]},
        {"source": "analytics.checkout", "metric": "abandoned_checkouts", "value": data["abandoned_checkouts"]},
        {"source": "analytics.checkout", "metric": "abandonment_rate", "value": data["abandonment_rate"]},
        {"source": "analytics.checkout", "metric": "abandoned_value", "value": data["abandoned_value"]},
    ])]
    return success_result("get_checkout_metrics", data, evidence)
