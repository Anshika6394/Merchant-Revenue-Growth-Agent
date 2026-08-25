"""Phase 6 - Revenue Leakage Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    PRIORITY_HIGH, PRIORITY_MEDIUM,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class RevenueLeakageAgent(BaseRevenueAgent):
    """Analyzes refund patterns to identify revenue leakage signals."""
    OPPORTUNITY_TYPE = "REFUND_LEAKAGE"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            data = self._call("get_refund_metrics", {}, db)
            if data is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            refund_count = data.get("refund_count", 0)
            refund_value = data.get("refund_value", 0)
            refund_rate = data.get("refund_rate", 0)
            reasons = data.get("refund_reasons", {})

            if refund_count == 0:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No refunds detected in the current period.",
                )

            # Find top refund reason
            top_reason = max(reasons, key=lambda k: float(reasons[k]), default="unknown") if reasons else "unknown"

            evidence = [
                {"source": "tool.get_refund_metrics", "metric": "refund_count", "value": refund_count},
                {"source": "tool.get_refund_metrics", "metric": "refund_value", "value": refund_value},
                {"source": "tool.get_refund_metrics", "metric": "refund_rate", "value": refund_rate},
                {"source": "tool.get_refund_metrics", "metric": "top_refund_reason", "value": top_reason},
            ]

            priority = PRIORITY_HIGH if float(refund_rate) > 0.05 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if refund_count > 5 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"{refund_count} refunds totalling {refund_value} detected "
                    f"(refund rate: {float(refund_rate):.1%}). "
                    f"Top reason: {top_reason}."
                ),
                root_cause=(
                    f"Elevated refund rate suggests product quality issues, "
                    f"mismatched customer expectations, or fulfilment problems. "
                    f"The most frequent refund reason is '{top_reason}'."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": refund_value,
                    "currency": "INR",
                    "basis": "Total refund value in current period",
                },
                recommended_action=(
                    f"Investigate the root cause of '{top_reason}' refunds. "
                    "Improve product descriptions, quality checks, and post-purchase support "
                    "to reduce refund rate below 2%."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    "Refund rate above 5% indicates a systemic issue requiring immediate attention.",
                    "Reducing refunds directly improves net revenue without additional acquisition cost.",
                    "Impact is the current refund value; future prevention depends on root cause fix.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
