"""Phase 6 - Product Growth Agent."""
from __future__ import annotations
from typing import Any
from app.agents.base_agent import (
    BaseRevenueAgent, CONFIDENCE_HIGH, CONFIDENCE_MEDIUM,
    PRIORITY_HIGH, PRIORITY_MEDIUM,
    build_agent_output, fallback_output, insufficient_evidence_output,
)


class ProductGrowthAgent(BaseRevenueAgent):
    """Identifies product-level growth opportunities from revenue distribution."""
    OPPORTUNITY_TYPE = "PRODUCT_GROWTH"

    def analyze(self, db: Any) -> dict[str, Any]:
        try:
            data = self._call("get_product_metrics", {}, db)
            if data is None:
                return fallback_output(self.OPPORTUNITY_TYPE)

            products = data.get("products", [])
            total_revenue = data.get("total_revenue", 0)
            total_products = data.get("total_products", 0)

            if total_products == 0 or not products:
                return insufficient_evidence_output(
                    self.OPPORTUNITY_TYPE,
                    "No product data available for the current period.",
                )

            top = products[0]
            top_name = top.get("name", "Unknown")
            top_revenue = top.get("revenue", 0)
            top_share = float(top_revenue) / float(total_revenue) if float(total_revenue) > 0 else 0

            # Low performers: products below 10% of top product revenue
            low_performers = [
                p for p in products
                if float(p.get("revenue", 0)) < float(top_revenue) * 0.1
            ]

            evidence = [
                {"source": "tool.get_product_metrics", "metric": "total_products", "value": total_products},
                {"source": "tool.get_product_metrics", "metric": "total_revenue", "value": total_revenue},
                {"source": "tool.get_product_metrics", "metric": "top_product", "value": top_name},
                {"source": "tool.get_product_metrics", "metric": "top_product_revenue", "value": top_revenue},
                {"source": "tool.get_product_metrics", "metric": "top_product_revenue_share", "value": round(top_share, 4)},
                {"source": "tool.get_product_metrics", "metric": "low_performer_count", "value": len(low_performers)},
            ]

            priority = PRIORITY_HIGH if top_share > 0.6 else PRIORITY_MEDIUM
            confidence = CONFIDENCE_HIGH if total_products > 2 else CONFIDENCE_MEDIUM

            return build_agent_output(
                opportunity_type=self.OPPORTUNITY_TYPE,
                summary=(
                    f"'{top_name}' drives {top_share:.1%} of total revenue ({top_revenue}). "
                    f"{len(low_performers)} of {total_products} products are underperforming."
                ),
                root_cause=(
                    f"Revenue is concentrated in '{top_name}', indicating over-reliance on a single product. "
                    f"{len(low_performers)} products generate less than 10% of the top product's revenue."
                ),
                evidence=evidence,
                estimated_impact={
                    "value": total_revenue,
                    "currency": "INR",
                    "basis": "Total product revenue; growth via mix optimization",
                },
                recommended_action=(
                    f"Promote underperforming products to customers who purchased '{top_name}'. "
                    "Bundle low-performers with top products. "
                    "Review pricing and visibility of underperforming SKUs."
                ),
                priority=priority,
                confidence=confidence,
                assumptions=[
                    "Revenue concentration above 60% in one product signals diversification risk.",
                    "Cross-sell to existing customers is more cost-effective than new acquisition.",
                    "Low-performer threshold set at 10% of top product revenue.",
                ],
            )
        except Exception:
            return fallback_output(self.OPPORTUNITY_TYPE)
