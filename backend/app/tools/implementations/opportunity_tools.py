"""Phase 5 - Tools: get_opportunities, get_opportunity_details."""
from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.agents.evidence_agent import EvidenceAgent
from app.services.tool_analytics import compute_opportunities, get_opportunity_by_id
from app.tools.base import error_result, success_result
from app.tools.schemas import GetOpportunitiesInput, OpportunityDetailsInput

_agent = EvidenceAgent()

def get_opportunities(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Ranked revenue opportunities from analytics."""
    try:
        params = GetOpportunitiesInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_opportunities", exc.errors()[0]["msg"])
    all_opps = compute_opportunities(db)
    if params.category != "all":
        all_opps = [o for o in all_opps if o["type"] == params.category]
    if params.min_impact is not None:
        all_opps = [o for o in all_opps if float(o["estimated_revenue_impact"]) >= params.min_impact]
    total_impact = sum(float(o["estimated_revenue_impact"]) for o in all_opps)
    data = {"opportunities": all_opps, "count": len(all_opps), "total_estimated_impact": total_impact}
    evidence = [_agent.build_insight("opportunities", len(all_opps), [
        {"source": "analytics.opportunities", "metric": "count", "value": len(all_opps)},
        {"source": "analytics.opportunities", "metric": "total_estimated_impact", "value": total_impact},
    ])]
    return success_result("get_opportunities", data, evidence)

def get_opportunity_details(db: Any, raw_params: dict[str, Any]) -> dict[str, Any]:
    """Full details for a single opportunity by opportunity_id."""
    try:
        params = OpportunityDetailsInput.model_validate(raw_params)
    except ValidationError as exc:
        return error_result("get_opportunity_details", exc.errors()[0]["msg"])
    opp = get_opportunity_by_id(db, params.opportunity_id)
    if opp is None:
        return error_result("get_opportunity_details", f"Opportunity '{params.opportunity_id}' not found.")
    evidence = [_agent.build_insight("opportunity_details", opp.get("estimated_revenue_impact"), [
        {"source": "analytics.opportunities", "metric": "opportunity_id", "value": params.opportunity_id},
        {"source": "analytics.opportunities", "metric": "estimated_revenue_impact", "value": opp.get("estimated_revenue_impact")},
        {"source": "analytics.opportunities", "metric": "confidence", "value": opp.get("confidence")},
    ])]
    return success_result("get_opportunity_details", opp, evidence)
