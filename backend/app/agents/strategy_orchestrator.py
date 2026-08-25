"""Phase 7 - Revenue Strategy Orchestrator Agent."""
from __future__ import annotations
from typing import Any

from app.agents import ALL_AGENTS
from app.agents.base_agent import (
    PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
    CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, CONFIDENCE_LOW,
)

INTENT_MAP = {
    "payment": ["PaymentRecoveryAgent"],
    "checkout": ["CheckoutRecoveryAgent"],
    "winback": ["WinbackAgent"],
    "win-back": ["WinbackAgent"],
    "churn": ["WinbackAgent"],
    "subscription": ["SubscriptionRetentionAgent"],
    "retention": ["SubscriptionRetentionAgent"],
    "refund": ["RevenueLeakageAgent"],
    "leakage": ["RevenueLeakageAgent"],
    "product": ["ProductGrowthAgent"],
    "growth": ["ProductGrowthAgent"],
    "conversion": ["ProductGrowthAgent"],
}

PRIORITY_RANK = {PRIORITY_HIGH: 3, PRIORITY_MEDIUM: 2, PRIORITY_LOW: 1}
CONFIDENCE_RANK = {CONFIDENCE_HIGH: 3, CONFIDENCE_MEDIUM: 2, CONFIDENCE_LOW: 1}


def _opportunity_score(result: dict[str, Any]) -> float:
    p = PRIORITY_RANK.get(result.get("priority", PRIORITY_LOW), 1)
    c = CONFIDENCE_RANK.get(result.get("confidence", CONFIDENCE_LOW), 1)
    impact = result.get("estimated_impact", {}).get("value", 0) or 0
    try:
        impact_score = min(float(impact) / 100000, 5.0)
    except (TypeError, ValueError):
        impact_score = 0.0
    return p * c * (1 + impact_score)


def _select_agents(query: str) -> list:
    query_lower = query.lower()
    matched = set()
    for keyword, agent_names in INTENT_MAP.items():
        if keyword in query_lower:
            for agent_cls in ALL_AGENTS:
                if agent_cls.__name__ in agent_names:
                    matched.add(agent_cls)
    return list(matched) if matched else list(ALL_AGENTS)


def _deduplicate(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for r in results:
        otype = r.get("opportunity_type", "UNKNOWN")
        if otype not in seen or _opportunity_score(r) > _opportunity_score(seen[otype]):
            seen[otype] = r
    return list(seen.values())


def _executive_summary(query: str, ranked: list[dict[str, Any]]) -> str:
    if not ranked:
        return "No significant revenue opportunities detected at this time."
    top = ranked[0]
    return (
        f"Based on your query '{query}', RevPilot AI identified "
        f"{len(ranked)} revenue opportunity(ies). "
        f"The highest priority opportunity is {top['opportunity_type']} "
        f"({top['priority']} priority, {top['confidence']} confidence): "
        f"{top['summary']}"
    )


class StrategyOrchestrator:
    """
    Phase 7 - Central Revenue Strategy Orchestrator.
    Coordinates specialized agents, ranks opportunities,
    and returns a merchant-ready strategic brief.
    Never fabricates financial values.
    """

    def __init__(self, registry: Any) -> None:
        self.registry = registry

    def run(self, query: str, db: Any) -> dict[str, Any]:
        if not query or not query.strip():
            return self._empty_response("No query provided.")

        selected_agent_classes = _select_agents(query)
        results: list[dict[str, Any]] = []
        errors: list[str] = []

        for agent_cls in selected_agent_classes:
            try:
                agent = agent_cls(self.registry)
                result = agent.analyze(db=db)
                result["_agent"] = agent_cls.__name__
                results.append(result)
            except Exception as exc:
                errors.append(f"{agent_cls.__name__}: {exc}")

        deduped = _deduplicate(results)
        ranked = sorted(deduped, key=_opportunity_score, reverse=True)
        top3 = ranked[:3]

        total_impact = sum(
            float(r.get("estimated_impact", {}).get("value", 0) or 0)
            for r in ranked
        )

        return {
            "query": query,
            "executive_summary": _executive_summary(query, ranked),
            "top_opportunities": top3,
            "all_opportunities": ranked,
            "total_estimated_impact": {
                "value": round(total_impact, 2),
                "currency": "INR",
                "basis": "sum_of_agent_estimates",
            },
            "recommended_next_steps": [
                r.get("recommended_action", "") for r in top3
            ],
            "agents_run": [cls.__name__ for cls in selected_agent_classes],
            "errors": errors,
            "assumptions": list({
                a
                for r in ranked
                for a in r.get("assumptions", [])
            }),
        }

    def _empty_response(self, reason: str) -> dict[str, Any]:
        return {
            "query": "",
            "executive_summary": reason,
            "top_opportunities": [],
            "all_opportunities": [],
            "total_estimated_impact": {"value": 0, "currency": "INR", "basis": "no_data"},
            "recommended_next_steps": [],
            "agents_run": [],
            "errors": [reason],
            "assumptions": [],
        }
