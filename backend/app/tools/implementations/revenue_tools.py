"""Phase 5 - Tools: get_revenue_overview, compare_periods."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.analytics import pct_change
from app.services.tool_analytics import revenue_for_period
from app.tools.base import error_result, success_result
from app.tools.schemas import ComparePeriodsInput, RevenueOverviewInput

_agent = EvidenceAgent()

def get_revenue_overview(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Gross revenue, net revenue, AOV, and order count for a date range."""
    try:
        params = RevenueOverviewInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_revenue_overview", exc.errors()[0]["msg"])
    data = revenue_for_period(db, params.start(), params.end())
    evidence = [_agent.build_insight("revenue_overview", data["gross_revenue"], [
        {"source": "analytics.revenue", "metric": "gross_revenue", "value": data["gross_revenue"]},
        {"source": "analytics.revenue", "metric": "net_revenue", "value": data["net_revenue"]},
        {"source": "analytics.revenue", "metric": "order_count", "value": data["order_count"]},
        {"source": "analytics.revenue", "metric": "aov", "value": data["aov"]},
        {"source": "analytics.revenue", "metric": "refunds_total", "value": data["refunds_total"]},
    ])]
    return success_result("get_revenue_overview", data, evidence)

def compare_periods(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Compare revenue metrics between two date periods."""
    try:
        params = ComparePeriodsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("compare_periods", exc.errors()[0]["msg"])
    current = revenue_for_period(db, params.start(), params.end())
    compare = revenue_for_period(db, params.cmp_start(), params.cmp_end())
    changes = {
        "gross_revenue_pct": pct_change(current["gross_revenue"], compare["gross_revenue"]),
        "net_revenue_pct": pct_change(current["net_revenue"], compare["net_revenue"]),
        "order_count_pct": pct_change(current["order_count"], compare["order_count"]),
        "aov_pct": pct_change(current["aov"], compare["aov"]),
    }
    data = {"current_period": current, "compare_period": compare, "changes": changes}
    evidence = [_agent.build_insight("compare_periods", changes["gross_revenue_pct"], [
        {"source": "analytics.revenue.current", "metric": "gross_revenue", "value": current["gross_revenue"]},
        {"source": "analytics.revenue.compare", "metric": "gross_revenue", "value": compare["gross_revenue"]},
        {"source": "analytics.revenue", "metric": "gross_revenue_pct_change", "value": changes["gross_revenue_pct"]},
        {"source": "analytics.revenue", "metric": "order_count_pct_change", "value": changes["order_count_pct"]},
    ])]
    return success_result("compare_periods", data, evidence)
