"""Phase 5 - Tools: get_payment_failures, get_recoverable_revenue."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.tool_analytics import payments_for_period
from app.tools.base import error_result, success_result
from app.tools.schemas import PaymentFailuresInput, RecoverableRevenueInput

_agent = EvidenceAgent()

def get_payment_failures(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Payment failure list with failure-rate analytics."""
    try:
        params = PaymentFailuresInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_payment_failures", exc.errors()[0]["msg"])
    data = payments_for_period(db, params.start(), params.end(), params.limit, params.offset)
    evidence = [_agent.build_insight("payment_failures", data["summary"]["failed"], [
        {"source": "analytics.payments", "metric": "total_payments", "value": data["summary"]["total"]},
        {"source": "analytics.payments", "metric": "failed_payments", "value": data["summary"]["failed"]},
        {"source": "analytics.payments", "metric": "failure_rate", "value": data["summary"]["failure_rate"]},
        {"source": "analytics.payments", "metric": "failed_value", "value": data["summary"]["failed_value"]},
        {"source": "analytics.payments", "metric": "recoverable_count", "value": data["recoverable"]["eligible_payment_count"]},
    ])]
    return success_result("get_payment_failures", data, evidence)

def get_recoverable_revenue(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Estimate revenue recoverable from retry-eligible failed payments."""
    try:
        RecoverableRevenueInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_recoverable_revenue", exc.errors()[0]["msg"])
    data = payments_for_period(db)
    recoverable = data["recoverable"]
    evidence = [_agent.build_insight("recoverable_revenue", recoverable["estimated_recoverable_revenue"], [
        {"source": "analytics.payments", "metric": "eligible_payment_count", "value": recoverable["eligible_payment_count"]},
        {"source": "analytics.payments", "metric": "eligible_customer_count", "value": recoverable["eligible_customer_count"]},
        {"source": "analytics.payments", "metric": "failed_value", "value": recoverable["failed_value"]},
        {"source": "analytics.payments", "metric": "recovery_assumption", "value": recoverable["recovery_assumption"]},
        {"source": "analytics.payments", "metric": "estimated_recoverable_revenue", "value": recoverable["estimated_recoverable_revenue"]},
    ])]
    return success_result("get_recoverable_revenue", {"recoverable": recoverable}, evidence)
