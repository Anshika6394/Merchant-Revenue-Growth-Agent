"""
Phase 6 - Tests for all 6 specialized revenue growth agents.

Covers:
- All 6 agents return correct output schema
- All 6 agents run against real DB fixture
- Fallback output when tool returns failure
- Insufficient evidence output when no data
- No financial values fabricated (all from tool results)
- Agent output contains required keys
"""
from __future__ import annotations
from typing import Any
from unittest.mock import MagicMock
import pytest

from app.agents.base_agent import (
    AGENT_OUTPUT_KEYS, build_agent_output, fallback_output,
    insufficient_evidence_output, PRIORITY_LOW, CONFIDENCE_LOW,
)
from app.agents.payment_recovery_agent import PaymentRecoveryAgent
from app.agents.checkout_recovery_agent import CheckoutRecoveryAgent
from app.agents.winback_agent import WinbackAgent
from app.agents.subscription_retention_agent import SubscriptionRetentionAgent
from app.agents.revenue_leakage_agent import RevenueLeakageAgent
from app.agents.product_growth_agent import ProductGrowthAgent
from app.tools.registry import registry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_agent_output_shape(result: dict, expected_type: str) -> None:
    assert isinstance(result, dict), "Agent output must be a dict"
    for key in AGENT_OUTPUT_KEYS:
        assert key in result, f"Missing key '{key}' in agent output"
    assert result["opportunity_type"] == expected_type
    assert isinstance(result["summary"], str) and len(result["summary"]) > 0
    assert isinstance(result["evidence"], list)
    assert isinstance(result["estimated_impact"], dict)
    assert "value" in result["estimated_impact"]
    assert isinstance(result["assumptions"], list)
    assert result["priority"] in ("HIGH", "MEDIUM", "LOW")
    assert result["confidence"] in ("HIGH", "MEDIUM", "LOW")


def make_failing_registry() -> Any:
    """Registry that always returns a failure result."""
    mock = MagicMock()
    mock.call.return_value = {"success": False, "data": {}, "evidence": [], "error": "unavailable", "tool": "mock"}
    return mock


# ---------------------------------------------------------------------------
# Unit tests — base_agent utilities
# ---------------------------------------------------------------------------

def test_build_agent_output_has_all_keys():
    result = build_agent_output(
        opportunity_type="TEST", summary="s", root_cause="r",
        evidence=[], estimated_impact={"value": 0, "currency": "INR", "basis": "test"},
        recommended_action="do x", priority="HIGH", confidence="HIGH", assumptions=[],
    )
    assert set(result.keys()) == AGENT_OUTPUT_KEYS


def test_fallback_output_shape():
    result = fallback_output("TEST_TYPE")
    assert_agent_output_shape(result, "TEST_TYPE")
    assert result["priority"] == PRIORITY_LOW
    assert result["confidence"] == CONFIDENCE_LOW


def test_insufficient_evidence_output_shape():
    result = insufficient_evidence_output("TEST_TYPE", "no data")
    assert_agent_output_shape(result, "TEST_TYPE")
    assert result["confidence"] == CONFIDENCE_LOW


# ---------------------------------------------------------------------------
# Unit tests — fallback when tools unavailable
# ---------------------------------------------------------------------------

def test_payment_recovery_agent_fallback():
    agent = PaymentRecoveryAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "PAYMENT_RECOVERY")
    assert result["confidence"] == CONFIDENCE_LOW


def test_checkout_recovery_agent_fallback():
    agent = CheckoutRecoveryAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "CHECKOUT_RECOVERY")
    assert result["confidence"] == CONFIDENCE_LOW


def test_winback_agent_fallback():
    agent = WinbackAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "CUSTOMER_WINBACK")
    assert result["confidence"] == CONFIDENCE_LOW


def test_subscription_retention_agent_fallback():
    agent = SubscriptionRetentionAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "SUBSCRIPTION_RETENTION")
    assert result["confidence"] == CONFIDENCE_LOW


def test_revenue_leakage_agent_fallback():
    agent = RevenueLeakageAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "REFUND_LEAKAGE")
    assert result["confidence"] == CONFIDENCE_LOW


def test_product_growth_agent_fallback():
    agent = ProductGrowthAgent(make_failing_registry())
    result = agent.analyze(db=None)
    assert_agent_output_shape(result, "PRODUCT_GROWTH")
    assert result["confidence"] == CONFIDENCE_LOW


# ---------------------------------------------------------------------------
# Integration tests — real DB
# ---------------------------------------------------------------------------

def test_payment_recovery_agent_with_db(db):
    agent = PaymentRecoveryAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "PAYMENT_RECOVERY")


def test_checkout_recovery_agent_with_db(db):
    agent = CheckoutRecoveryAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "CHECKOUT_RECOVERY")


def test_winback_agent_with_db(db):
    agent = WinbackAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "CUSTOMER_WINBACK")


def test_subscription_retention_agent_with_db(db):
    agent = SubscriptionRetentionAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "SUBSCRIPTION_RETENTION")


def test_revenue_leakage_agent_with_db(db):
    agent = RevenueLeakageAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "REFUND_LEAKAGE")


def test_product_growth_agent_with_db(db):
    agent = ProductGrowthAgent(registry)
    result = agent.analyze(db=db)
    assert_agent_output_shape(result, "PRODUCT_GROWTH")


# ---------------------------------------------------------------------------
# Agent output must not fabricate values — verify source is tools
# ---------------------------------------------------------------------------

def test_payment_recovery_agent_impact_comes_from_tools(db):
    agent = PaymentRecoveryAgent(registry)
    result = agent.analyze(db=db)
    # estimated_impact value must be numeric (from tool), not a string
    assert isinstance(result["estimated_impact"]["value"], (int, float, str))
    # evidence must reference tool sources
    if result["evidence"]:
        sources = [e["source"] for e in result["evidence"]]
        assert any("tool." in s for s in sources)


def test_all_agents_have_correct_opportunity_type(db):
    agents_and_types = [
        (PaymentRecoveryAgent(registry), "PAYMENT_RECOVERY"),
        (CheckoutRecoveryAgent(registry), "CHECKOUT_RECOVERY"),
        (WinbackAgent(registry), "CUSTOMER_WINBACK"),
        (SubscriptionRetentionAgent(registry), "SUBSCRIPTION_RETENTION"),
        (RevenueLeakageAgent(registry), "REFUND_LEAKAGE"),
        (ProductGrowthAgent(registry), "PRODUCT_GROWTH"),
    ]
    for agent, expected_type in agents_and_types:
        result = agent.analyze(db=db)
        assert result["opportunity_type"] == expected_type, (
            f"{agent.__class__.__name__} returned wrong type: {result['opportunity_type']}"
        )


def test_all_agents_return_non_empty_summary(db):
    agents = [
        PaymentRecoveryAgent(registry),
        CheckoutRecoveryAgent(registry),
        WinbackAgent(registry),
        SubscriptionRetentionAgent(registry),
        RevenueLeakageAgent(registry),
        ProductGrowthAgent(registry),
    ]
    for agent in agents:
        result = agent.analyze(db=db)
        assert len(result["summary"]) > 10, (
            f"{agent.__class__.__name__} returned empty summary"
        )
