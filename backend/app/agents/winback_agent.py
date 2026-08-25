"""Phase 6 - Customer Win-back Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class WinbackAgent(BaseRevenueAgent):
    """Identifies churned customers and estimates win-back revenue."""
    OPPORTUNITY_TYPE = "CUSTOMER_WINBACK"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            metrics = self._call("get_customer_metrics", {}, db)
            candidates = self._call("get_winback_candidates", {"min_days_inactive": 90, "limit": 200}, db)

            if metrics is None or candidates is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            inactive = metrics.get("inactive_customers", 0)
            win_back_signals = metrics.get("win_back_signals", 0)
            count = candidates.get("count", 0)
            spend_at_risk = candidates.get("total_spend_at_risk", 0)

            if count == 0:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No win-back candidates found in the current period.",
                )

            recovery_rate = 0.10
            estimated_recovery = float(spend_at_risk) * recovery_rate

            evidence = [
                {"source": "tool.get_customer_metrics", "metric": "inactive_customers", "value": inactive},
                {"source": "tool.get_customer_metrics", "metric": "win_back_signals", "value": win_back_signals},
                {"source": "tool.get_winback_candidates", "metric": "candidate_count", "value": count},
                {"source": "tool.get_winback_candidates", "metric": "total_spend_at_risk", "value": spend_at_risk},
            ]

            priority = PRIORITY_HIGH if count > 20 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if count > 10 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"{count} customers have been inactive for 90+ days, "
                    f"representing {spend_at_risk} in historical lifetime spend at risk."
                ),
                root_cause=(
                    "Customer inactivity may indicate dissatisfaction, competitive loss, "
                    "or lifecycle end. High-value inactive customers represent the best win-back ROI."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": round(estimated_recovery, 2),
                    "currency": "INR",
                    "basis": f"{int(recovery_rate * 100)}% win-back rate on at-risk lifetime spend",
                },
                recommended_action=(
                    f"Launch a targeted win-back campaign for the top {min(count, 50)} "
                    "inactive customers ranked by lifetime spend. "
                    "Offer a personalized incentive or discount."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    f"Win-back conversion rate estimated at {int(recovery_rate * 100)}%.",
                    "Customers inactive for 90+ days are classified as churned.",
                    "Impact based on historical lifetime spend, not future projections.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
