"""Phase 6 - Checkout Recovery Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    PRIORITY_HIGH, PRIORITY_MEDIUM,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class CheckoutRecoveryAgent(BaseRevenueAgent):
    """Analyzes checkout abandonment and estimates recovery opportunity."""
    OPPORTUNITY_TYPE = "CHECKOUT_RECOVERY"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            data = self._call("get_checkout_metrics", {}, db)
            if data is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            starts = data.get("checkout_starts", 0)
            abandoned = data.get("abandoned_checkouts", 0)
            abandonment_rate = data.get("abandonment_rate", 0)
            abandoned_value = data.get("abandoned_value", 0)
            completed = data.get("completed_checkouts", 0)

            if starts == 0:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No checkout activity detected in the current period.",
                )

            # Conservative 15% recovery estimate on abandoned value
            recovery_rate = 0.15
            estimated_recovery = float(abandoned_value) * recovery_rate

            evidence = [
                {"source": "tool.get_checkout_metrics", "metric": "checkout_starts", "value": starts},
                {"source": "tool.get_checkout_metrics", "metric": "completed_checkouts", "value": completed},
                {"source": "tool.get_checkout_metrics", "metric": "abandoned_checkouts", "value": abandoned},
                {"source": "tool.get_checkout_metrics", "metric": "abandonment_rate", "value": abandonment_rate},
                {"source": "tool.get_checkout_metrics", "metric": "abandoned_value", "value": abandoned_value},
            ]

            priority = PRIORITY_HIGH if float(abandonment_rate) > 0.4 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if abandoned > 10 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"{abandoned} of {starts} checkouts were abandoned "
                    f"({float(abandonment_rate):.1%} abandonment rate), "
                    f"representing {abandoned_value} in lost revenue."
                ),
                root_cause=(
                    "High checkout abandonment is typically caused by friction in the payment "
                    "flow, unexpected costs at checkout, or session timeouts."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": round(estimated_recovery, 2),
                    "currency": "INR",
                    "basis": f"{int(recovery_rate * 100)}% recovery rate on abandoned checkout value",
                },
                recommended_action=(
                    "Send cart recovery emails within 1 hour of abandonment. "
                    "Simplify the checkout flow and display trust signals."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    f"Recovery rate estimated at {int(recovery_rate * 100)}% based on industry benchmarks.",
                    "Abandoned value includes only sessions with items added to cart.",
                    "Email recovery effectiveness depends on customer opt-in rate.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
