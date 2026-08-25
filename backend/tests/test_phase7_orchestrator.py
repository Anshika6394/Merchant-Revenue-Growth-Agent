"""Phase 7 - Strategy Orchestrator tests."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from app.agents.strategy_orchestrator import (
    StrategyOrchestrator, _opportunity_score, _select_agents, _deduplicate,
)
from app.agents.base_agent import PRIORITY_HIGH, PRIORITY_LOW, CONFIDENCE_HIGH, CONFIDENCE_LOW


def make_result(opportunity_type, priority=PRIORITY_LOW, confidence=CONFIDENCE_LOW, value=0):
    return {
        "opportunity_type": opportunity_type,
        "summary": f"Summary for {opportunity_type}",
        "root_cause": "Test root cause",
        "evidence": [],
        "estimated_impact": {"value": value, "currency": "INR", "basis": "test"},
        "recommended_action": "Take action",
        "priority": priority,
        "confidence": confidence,
        "assumptions": ["Test assumption"],
    }


def make_registry(results: dict):
    registry = MagicMock()
    def call(tool_name, params, db=None):
        return {"success": True, "data": results.get(tool_name, {})}
    registry.call.side_effect = call
    return registry


# --- Unit tests ---

def test_opportunity_score_high_beats_low():
    high = make_result("A", PRIORITY_HIGH, CONFIDENCE_HIGH, 500000)
    low = make_result("B", PRIORITY_LOW, CONFIDENCE_LOW, 0)
    assert _opportunity_score(high) > _opportunity_score(low)


def test_opportunity_score_impact_matters():
    a = make_result("A", PRIORITY_HIGH, CONFIDENCE_HIGH, 1000000)
    b = make_result("B", PRIORITY_HIGH, CONFIDENCE_HIGH, 0)
    assert _opportunity_score(a) > _opportunity_score(b)


def test_select_agents_payment_keyword():
    agents = _select_agents("How can I recover payment failures?")
    names = [a.__name__ for a in agents]
    assert "PaymentRecoveryAgent" in names


def test_select_agents_checkout_keyword():
    agents = _select_agents("Fix my checkout abandonment")
    names = [a.__name__ for a in agents]
    assert "CheckoutRecoveryAgent" in names


def test_select_agents_no_keyword_returns_all():
    from app.agents import ALL_AGENTS
    agents = _select_agents("What should I do today?")
    assert len(agents) == len(ALL_AGENTS)


def test_deduplicate_keeps_highest_score():
    r1 = make_result("PAYMENT_RECOVERY", PRIORITY_HIGH, CONFIDENCE_HIGH, 100000)
    r2 = make_result("PAYMENT_RECOVERY", PRIORITY_LOW, CONFIDENCE_LOW, 0)
    result = _deduplicate([r1, r2])
    assert len(result) == 1
    assert result[0]["priority"] == PRIORITY_HIGH


def test_deduplicate_keeps_different_types():
    r1 = make_result("PAYMENT_RECOVERY")
    r2 = make_result("CHECKOUT_RECOVERY")
    result = _deduplicate([r1, r2])
    assert len(result) == 2


# --- Orchestrator integration tests ---

def test_orchestrator_empty_query():
    orch = StrategyOrchestrator(MagicMock())
    result = orch.run("", db=MagicMock())
    assert result["executive_summary"] == "No query provided."
    assert result["top_opportunities"] == []


def test_orchestrator_returns_required_keys():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("What should I focus on today?", db=MagicMock())
    required = {
        "query", "executive_summary", "top_opportunities", "all_opportunities",
        "total_estimated_impact", "recommended_next_steps", "agents_run",
        "errors", "assumptions",
    }
    assert required.issubset(result.keys())


def test_orchestrator_query_stored():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("Where am I losing revenue?", db=MagicMock())
    assert result["query"] == "Where am I losing revenue?"


def test_orchestrator_top_opportunities_max_3():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("What should I do today?", db=MagicMock())
    assert len(result["top_opportunities"]) <= 3


def test_orchestrator_total_impact_is_numeric():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("How can I increase revenue?", db=MagicMock())
    assert isinstance(result["total_estimated_impact"]["value"], (int, float))


def test_orchestrator_agents_run_listed():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("Fix payment failures", db=MagicMock())
    assert "PaymentRecoveryAgent" in result["agents_run"]


def test_orchestrator_recommended_next_steps_match_top():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("What should I focus on today?", db=MagicMock())
    assert len(result["recommended_next_steps"]) <= 3


def test_orchestrator_no_duplicate_opportunity_types():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("What should I do today?", db=MagicMock())
    types = [r["opportunity_type"] for r in result["all_opportunities"]]
    assert len(types) == len(set(types))


def test_orchestrator_executive_summary_not_empty():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("Where am I losing revenue?", db=MagicMock())
    assert len(result["executive_summary"]) > 0


def test_orchestrator_currency_is_inr():
    registry = make_registry({})
    orch = StrategyOrchestrator(registry)
    result = orch.run("What should I focus on?", db=MagicMock())
    assert result["total_estimated_impact"]["currency"] == "INR"
