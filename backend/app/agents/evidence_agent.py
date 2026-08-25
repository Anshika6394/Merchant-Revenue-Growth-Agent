from typing import Any


class EvidenceAgent:
    """Builds evidence-backed insights from existing analytics data."""

    def build_insight(
        self,
        metric: str,
        value: Any,
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "metric": metric,
            "value": value,
            "evidence": evidence,
        }

    def analyze_revenue(self, analytics: dict[str, Any]) -> dict[str, Any]:
        """Create a deterministic revenue insight using existing analytics evidence."""
        gross_revenue = analytics.get("gross_revenue")
        net_revenue = analytics.get("net_revenue")
        order_count = analytics.get("order_count")
        aov = analytics.get("aov")

        evidence = [
            {"source": "analytics.revenue", "metric": "gross_revenue", "value": gross_revenue},
            {"source": "analytics.revenue", "metric": "net_revenue", "value": net_revenue},
            {"source": "analytics.revenue", "metric": "order_count", "value": order_count},
            {"source": "analytics.revenue", "metric": "aov", "value": aov},
        ]

        return {
            "insight_type": "revenue",
            "summary": "Revenue performance is derived from the analytics metrics.",
            "evidence": evidence,
        }
