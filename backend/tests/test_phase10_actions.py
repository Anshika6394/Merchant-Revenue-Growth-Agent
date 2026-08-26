"""Phase 10 - Action Simulator tests."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.action_simulator import simulate_action, get_actions, submit_feedback
from app.models.simulated_action import ActionStatus

def make_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.order_by.return_value.all.return_value = []
    return db

def test_simulate_retry_payment():
    db = make_db()
    result = simulate_action(db, "opp-1", "retry_payment", 50, 5000)
    assert result["action_type"] == "retry_payment"
    assert result["target_count"] == 50
    assert result["estimated_revenue"] > 0
    assert result["label"] == "SIMULATED"
    assert db.add.called
    assert db.commit.called

def test_simulate_checkout_recovery():
    db = make_db()
    result = simulate_action(db, None, "checkout_recovery", 30, 3000)
    assert result["action_type"] == "checkout_recovery"
    assert result["estimated_revenue"] > 0

def test_simulate_winback():
    db = make_db()
    result = simulate_action(db, None, "winback_campaign", 20, 8000)
    assert result["estimated_conversions"] > 0
    assert result["roi_percent"] is not None

def test_simulate_subscription_retention():
    db = make_db()
    result = simulate_action(db, None, "subscription_retention", 15, 2500)
    assert result["expected_conversion"] == 0.65

def test_simulate_product_promotion():
    db = make_db()
    result = simulate_action(db, None, "product_promotion", 100, 1500)
    assert result["estimated_cost"] == 1500.0

def test_simulation_result_labeled_simulated():
    db = make_db()
    result = simulate_action(db, None, "retry_payment", 10, 1000)
    assert "SIMULATED" in result["simulation_result"]

def test_simulate_roi_positive():
    db = make_db()
    result = simulate_action(db, None, "subscription_retention", 10, 5000)
    assert result["roi_percent"] > 0

def test_get_actions_empty():
    db = make_db()
    result = get_actions(db)
    assert result == []

def test_feedback_not_found():
    db = make_db()
    result = submit_feedback(db, "nonexistent", "good", "successful")
    assert "error" in result

def test_feedback_updates_action():
    from app.models.simulated_action import SimulatedAction
    db = MagicMock()
    mock_action = MagicMock(spec=SimulatedAction)
    mock_action.id = "abc"
    mock_action.feedback = None
    mock_action.status = "simulated"
    mock_action.opportunity_id = None
    mock_action.action_type = "retry_payment"
    mock_action.target_count = 10
    mock_action.estimated_cost = 50
    mock_action.estimated_revenue = 200
    mock_action.expected_conversion = 0.28
    mock_action.simulation_result = "test"
    mock_action.created_at = "2026-01-01"
    db.query.return_value.filter.return_value.first.return_value = mock_action
    result = submit_feedback(db, "abc", "worked great", "successful")
    assert mock_action.feedback == "worked great"
    assert mock_action.status == "successful"
