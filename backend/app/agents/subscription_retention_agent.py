"""Phase 6 - Subscription Retention Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    PRIORITY_HIGH, PRIORITY_MEDIUM,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class SubscriptionRetentionAgent(BaseRevenueAgent):
    """Identifies at-risk subscriptions and estimates MRR at risk."""
    OPPORTUNITY_TYPE = "SUBSCRIPTION_RETENTION"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            data = self._call("get_subscription_risks", {}, db)
            if data is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            count = data.get("count", 0)
            at_risk_mrr = data.get("total_at_risk_mrr", 0)
            global_stats = data.get("global_stats", {})
            retention_risk = global_stats.get("retention_risk", 0)

            if count == 0:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No at-risk subscriptions detected.",
                )

            recovery_rate = 0.35
            estimated_recovery = float(at_risk_mrr) * recovery_rate

            evidence = [
                {"source": "tool.get_subscription_risks", "metric": "at_risk_count", "value": count},
                {"source": "tool.get_subscription_risks", "metric": "total_at_risk_mrr", "value": at_risk_mrr},
                {"source": "tool.get_subscription_risks", "metric": "retention_risk", "value": retention_risk},
            ]

            priority = PRIORITY_HIGH if float(at_risk_mrr) > 0 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if count > 5 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"{count} subscriptions are at risk of churning, "
                    f"representing {at_risk_mrr} in monthly recurring revenue."
                ),
                root_cause=(
                    "Subscriptions with past-due payments or repeated payment failures "
                    "are at high risk of involuntary churn. Early intervention significantly "
                    "improves retention rates."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": round(estimated_recovery, 2),
                    "currency": "INR",
                    "basis": f"{int(recovery_rate * 100)}% retention rate on at-risk MRR",
                },
                recommended_action=(
                    "Contact at-risk subscribers immediately with payment update requests. "
                    "Offer a grace period or payment plan for past-due accounts."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    f"Retention rate estimated at {int(recovery_rate * 100)}% with proactive outreach.",
                    "MRR values are based on current subscription amounts.",
                    "Past-due subscriptions are more likely to churn without intervention.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
