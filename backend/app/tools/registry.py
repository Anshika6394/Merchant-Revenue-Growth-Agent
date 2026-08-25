"""
Phase 5 – Tool Registry.

Central registry for all 12 RevPilot tools.
LLM agents discover and call tools through this registry.
No database access here — tools receive db sessions from callers.
"""
from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from app.tools.base import error_result
from app.tools.implementations.checkout_tools import get_checkout_metrics
from app.tools.implementations.customer_tools import get_customer_metrics, get_winback_candidates
from app.tools.implementations.opportunity_tools import get_opportunities, get_opportunity_details
from app.tools.implementations.payment_tools import get_payment_failures, get_recoverable_revenue
from app.tools.implementations.product_tools import get_product_metrics, get_refund_metrics
from app.tools.implementations.revenue_tools import compare_periods, get_revenue_overview
from app.tools.implementations.subscription_tools import get_subscription_risks
from app.tools.schemas import (
    CheckoutMetricsInput,
    ComparePeriodsInput,
    CustomerMetricsInput,
    GetOpportunitiesInput,
    OpportunityDetailsInput,
    PaymentFailuresInput,
    ProductMetricsInput,
    RecoverableRevenueInput,
    RefundMetricsInput,
    RevenueOverviewInput,
    SubscriptionRisksInput,
    WinbackCandidatesInput,
)


class ToolRegistry:
    """
    Centralized registry for RevPilot AI tools.

    Usage
    -----
    from app.tools.registry import registry

    # Discover tools (for LLM agent system prompt)
    tools = registry.list_tools()

    # Call a tool
    result = registry.call("get_revenue_overview", params={}, db=db_session)
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: type,
        fn: Callable[[Session, dict[str, Any]], dict[str, Any]],
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "fn": fn,
        }

    def call(
        self,
        tool_name: str,
        params: dict[str, Any],
        db: Session | None = None,
    ) -> dict[str, Any]:
        """Call a registered tool by name."""
        if tool_name not in self._tools:
            return error_result(tool_name, f"Unknown tool: '{tool_name}'. Call list_tools() to see available tools.")
        try:
            return self._tools[tool_name]["fn"](db, params)
        except Exception:
            return error_result(tool_name, "Tool execution failed. Please check your inputs.")

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool metadata for LLM agent discovery."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"].model_json_schema(),
            }
            for t in self._tools.values()
        ]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ---------------------------------------------------------------------------
# Module-level registry instance — import and use directly
# ---------------------------------------------------------------------------

registry = ToolRegistry()

registry.register(
    name="get_revenue_overview",
    description="Return gross revenue, net revenue, AOV, and order count for a date range.",
    input_schema=RevenueOverviewInput,
    fn=get_revenue_overview,
)
registry.register(
    name="get_payment_failures",
    description="Return paginated payment failure list with failure-rate analytics.",
    input_schema=PaymentFailuresInput,
    fn=get_payment_failures,
)
registry.register(
    name="get_recoverable_revenue",
    description="Estimate revenue recoverable from retry-eligible failed payments.",
    input_schema=RecoverableRevenueInput,
    fn=get_recoverable_revenue,
)
registry.register(
    name="get_checkout_metrics",
    description="Return checkout funnel metrics: starts, completions, abandonment rate and value.",
    input_schema=CheckoutMetricsInput,
    fn=get_checkout_metrics,
)
registry.register(
    name="get_customer_metrics",
    description="Return customer health metrics: active, inactive, repeat, high-value counts.",
    input_schema=CustomerMetricsInput,
    fn=get_customer_metrics,
)
registry.register(
    name="get_winback_candidates",
    description="List customers inactive beyond threshold, ranked by lifetime spend.",
    input_schema=WinbackCandidatesInput,
    fn=get_winback_candidates,
)
registry.register(
    name="get_subscription_risks",
    description="List subscriptions at risk of churn: past-due and failed-payment subscriptions.",
    input_schema=SubscriptionRisksInput,
    fn=get_subscription_risks,
)
registry.register(
    name="get_refund_metrics",
    description="Return refund count, total value, refund rate, and reason breakdown.",
    input_schema=RefundMetricsInput,
    fn=get_refund_metrics,
)
registry.register(
    name="get_product_metrics",
    description="Return per-product revenue, order count, optionally filtered by product name.",
    input_schema=ProductMetricsInput,
    fn=get_product_metrics,
)
registry.register(
    name="get_opportunities",
    description="Return ranked revenue opportunities detected from analytics data.",
    input_schema=GetOpportunitiesInput,
    fn=get_opportunities,
)
registry.register(
    name="get_opportunity_details",
    description="Return full details for a single opportunity by opportunity_id.",
    input_schema=OpportunityDetailsInput,
    fn=get_opportunity_details,
)
registry.register(
    name="compare_periods",
    description="Compare revenue metrics between two date periods with percentage changes.",
    input_schema=ComparePeriodsInput,
    fn=compare_periods,
)
