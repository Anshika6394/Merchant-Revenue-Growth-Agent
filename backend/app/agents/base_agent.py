"""Phase 6 - Base class for all specialized revenue growth agents."""
from __future__ import annotations
from typing import Any


AGENT_OUTPUT_KEYS = {
    "opportunity_type", "summary", "root_cause", "evidence",
    "estimated_impact", "recommended_action", "priority", "confidence", "assumptions",
}

PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"


def build_agent_output(
    opportunity_type: str,
    summary: str,
    root_cause: str,
    evidence: list[dict[str, Any]],
    estimated_impact: dict[str, Any],
    recommended_action: str,
    priority: str,
    confidence: str,
    assumptions: list[str],
) -> dict[str, Any]:
    """Build a validated, structured agent output dict."""
    return {
        "opportunity_type": opportunity_type,
        "summary": summary,
        "root_cause": root_cause,
        "evidence": evidence,
        "estimated_impact": estimated_impact,
        "recommended_action": recommended_action,
        "priority": priority,
        "confidence": confidence,
        "assumptions": assumptions,
    }


def insufficient_evidence_output(opportunity_type: str, reason: str) -> dict[str, Any]:
    """Return a structured output when evidence is insufficient."""
    return build_agent_output(
        opportunity_type=opportunity_type,
        summary="Insufficient evidence to generate a recommendation.",
        root_cause=reason,
        evidence=[],
        estimated_impact={"value": 0, "currency": "INR", "basis": "insufficient_data"},
        recommended_action="Gather more data before taking action.",
        priority=PRIORITY_LOW,
        confidence=CONFIDENCE_LOW,
        assumptions=["No data available for this analysis period."],
    )


def fallback_output(opportunity_type: str) -> dict[str, Any]:
    """Return a safe fallback output when tools or LLM are unavailable."""
    return build_agent_output(
        opportunity_type=opportunity_type,
        summary="Agent could not complete analysis due to a system error.",
        root_cause="Tool or analytics service unavailable.",
        evidence=[],
        estimated_impact={"value": 0, "currency": "INR", "basis": "unavailable"},
        recommended_action="Retry after the system recovers.",
        priority=PRIORITY_LOW,
        confidence=CONFIDENCE_LOW,
        assumptions=["Analysis requires analytics tools to be available."],
    )


class BaseRevenueAgent:
    """
    Base class for all Phase 6 specialized revenue agents.
    Agents call tools via the registry and return structured output.
    Agents never fabricate financial values.
    """
    OPPORTUNITY_TYPE: str = "UNKNOWN"

    def __init__(self, registry: Any) -> None:
        self.registry = registry

    def _call(self, tool_name: str, params: dict[str, Any], db: Any) -> dict[str, Any] | None:
        """Call a tool and return its data, or None on failure."""
        try:
            result = self.registry.call(tool_name, params, db=db)
            if result.get("success"):
                return result["data"]
            return None
        except Exception:
            return None

    def analyze(self, db: Any) -> dict[str, Any]:
        """Run the agent analysis. Override in subclasses."""
        raise NotImplementedError
