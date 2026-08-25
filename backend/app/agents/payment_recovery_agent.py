"""Phase 6 - Payment Recovery Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
    PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class PaymentRecoveryAgent(BaseRevenueAgent):
    """
    Analyzes failed payments and estimates recoverable revenue.
    All financial values come from tool results — never fabricated.
    """
    OPPORTUNITY_TYPE = "PAYMENT_RECOVERY"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            failures = self._call("get_payment_failures", {}, db)
            recoverable = self._call("get_recoverable_revenue", {}, db)

            if failures is None or recoverable is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            summary = failures.get("summary", {})
            rec = recoverable.get("recoverable", {})

            failed_count = summary.get("failed", 0)
            failure_rate = summary.get("failure_rate", 0)
            failed_value = summary.get("failed_value", 0)
            eligible_count = rec.get("eligible_payment_count", 0)
            recoverable_revenue = rec.get("estimated_recoverable_revenue", 0)
            recovery_assumption = rec.get("recovery_assumption", 0)

            if failed_count == 0:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No failed payments detected in the current period.",
                )

            evidence = [
                {"source": "tool.get_payment_failures", "metric": "failed_payments", "value": failed_count},
                {"source": "tool.get_payment_failures", "metric": "failure_rate", "value": failure_rate},
                {"source": "tool.get_payment_failures", "metric": "failed_value", "value": failed_value},
                {"source": "tool.get_recoverable_revenue", "metric": "eligible_payment_count", "value": eligible_count},
                {"source": "tool.get_recoverable_revenue", "metric": "estimated_recoverable_revenue", "value": recoverable_revenue},
            ]

            priority = PRIORITY_HIGH if float(failure_rate) > 0.1 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if eligible_count > 0 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"{failed_count} failed payments detected with a failure rate of "
                    f"{float(failure_rate):.1%}. Estimated recoverable revenue: {recoverable_revenue}."
                ),
                root_cause=(
                    "Payment failures may be caused by insufficient funds, expired cards, "
                    "or gateway timeouts. Retry-eligible payments can be recovered."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": recoverable_revenue,
                    "currency": "INR",
                    "basis": f"{float(recovery_assumption):.0%} recovery rate on eligible failed payments",
                },
                recommended_action=(
                    f"Initiate a retry campaign for {eligible_count} eligible failed payments. "
                    "Send payment update reminders to affected customers."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    f"Recovery rate assumed at {float(recovery_assumption):.0%} based on historical data.",
                    "Only retry-eligible payments are included in the estimate.",
                    "Actual recovery may vary based on customer response.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
