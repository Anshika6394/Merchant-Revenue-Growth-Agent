"""Phase 5 - Tools: get_product_metrics, get_refund_metrics."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.tool_analytics import products_for_period, refunds_for_period
from app.tools.base import error_result, success_result
from app.tools.schemas import ProductMetricsInput, RefundMetricsInput

_agent = EvidenceAgent()

def get_product_metrics(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Product-level revenue metrics."""
    try:
        params = ProductMetricsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_product_metrics", exc.errors()[0]["msg"])
    data = products_for_period(db, params.start(), params.end(), params.product_name)
    top = data["products"][0] if data["products"] else {}
    evidence = [_agent.build_insight("product_metrics", data["total_revenue"], [
        {"source": "analytics.products", "metric": "total_products", "value": data["total_products"]},
        {"source": "analytics.products", "metric": "total_revenue", "value": data["total_revenue"]},
        {"source": "analytics.products", "metric": "top_product", "value": top.get("name", "N/A")},
        {"source": "analytics.products", "metric": "top_product_revenue", "value": top.get("revenue", 0)},
    ])]
    return success_result("get_product_metrics", data, evidence)

def get_refund_metrics(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Refund metrics - count, value, rate, reasons."""
    try:
        params = RefundMetricsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_refund_metrics", exc.errors()[0]["msg"])
    data = refunds_for_period(db, params.start(), params.end())
    evidence = [_agent.build_insight("refund_metrics", data["refund_count"], [
        {"source": "analytics.refunds", "metric": "refund_count", "value": data["refund_count"]},
        {"source": "analytics.refunds", "metric": "refund_value", "value": data["refund_value"]},
        {"source": "analytics.refunds", "metric": "refund_rate", "value": data["refund_rate"]},
    ])]
    return success_result("get_refund_metrics", data, evidence)
