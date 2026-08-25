"""
Phase 5 – Comprehensive tests for the Safe Tool Layer.

Covers:
- All 12 tools execute successfully
- Input validation (bad dates, bad enums, bad ranges)
- Evidence always present on success
- Structured response format (success/tool/data/evidence/error)
- No secrets in error messages
- Registry has exactly 12 tools
- Tool files do NOT import from app.db.session
"""
from __future__ import annotations

import pathlib
import pytest

from app.tools.registry import registry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"success", "tool", "data", "evidence", "error"}
ALL_TOOL_NAMES = [
    "get_revenue_overview", "get_payment_failures", "get_recoverable_revenue",
    "get_checkout_metrics", "get_customer_metrics", "get_winback_candidates",
    "get_subscription_risks", "get_refund_metrics", "get_product_metrics",
    "get_opportunities", "get_opportunity_details", "compare_periods",
]

def assert_response_shape(result: dict, tool_name: str) -> None:
    assert isinstance(result, dict), "Result must be a dict"
    assert REQUIRED_KEYS == set(result.keys()), f"Missing keys in {tool_name} result"
    assert result["tool"] == tool_name

def assert_success(result: dict) -> None:
    assert result["success"] is True, f"Expected success, got error: {result.get('error')}"
    assert isinstance(result["data"], dict)
    assert isinstance(result["evidence"], list)
    assert len(result["evidence"]) > 0, "Evidence must be non-empty on success"
    assert result["error"] is None

def assert_failure(result: dict) -> None:
    assert result["success"] is False
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0
    assert result["data"] == {}
    assert result["evidence"] == []


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_registry_has_exactly_12_tools():
    assert len(registry) == 12

def test_registry_contains_all_tool_names():
    for name in ALL_TOOL_NAMES:
        assert name in registry, f"Tool '{name}' missing from registry"

def test_list_tools_returns_12_entries():
    tools = registry.list_tools()
    assert len(tools) == 12

def test_list_tools_schema_structure():
    for t in registry.list_tools():
        assert "name" in t
        assert "description" in t
        assert "input_schema" in t
        assert isinstance(t["description"], str) and len(t["description"]) > 5

def test_unknown_tool_returns_safe_error():
    result = registry.call("does_not_exist", {}, db=None)
    assert_response_shape(result, "does_not_exist")
    assert_failure(result)
    assert "does_not_exist" in result["error"] or "Unknown" in result["error"]


# ---------------------------------------------------------------------------
# Security: no secrets in errors
# ---------------------------------------------------------------------------

SECRETS = [
    "secret_key", "jwt_secret", "password", "database_url",
    "sqlalchemy", "traceback", "sessionlocal",
]

def test_no_secrets_in_bad_date_error():
    result = registry.call("get_revenue_overview", {"start_date": "not-a-date"}, db=None)
    assert result["success"] is False
    err = result["error"].lower()
    for s in SECRETS:
        assert s not in err, f"Secret pattern '{s}' found in error message"

def test_no_secrets_in_unknown_tool_error():
    result = registry.call("hack_attempt_secret_key", {}, db=None)
    err = result["error"].lower()
    for s in SECRETS:
        assert s not in err


# ---------------------------------------------------------------------------
# Input validation — date format
# ---------------------------------------------------------------------------

DATE_TOOLS_WITH_DATES = [
    "get_revenue_overview", "get_payment_failures",
    "get_checkout_metrics", "get_customer_metrics",
    "get_refund_metrics", "get_product_metrics",
]

@pytest.mark.parametrize("tool_name", DATE_TOOLS_WITH_DATES)
def test_invalid_date_format_rejected(tool_name):
    result = registry.call(tool_name, {"start_date": "01-01-2024"}, db=None)
    assert_response_shape(result, tool_name)
    assert_failure(result)

@pytest.mark.parametrize("tool_name", DATE_TOOLS_WITH_DATES)
def test_start_after_end_rejected(tool_name):
    result = registry.call(tool_name, {"start_date": "2024-12-31", "end_date": "2024-01-01"}, db=None)
    assert_response_shape(result, tool_name)
    assert_failure(result)

def test_compare_periods_invalid_date_rejected():
    result = registry.call("compare_periods", {
        "start_date": "bad", "end_date": "2024-01-31",
        "compare_start": "2023-12-01", "compare_end": "2023-12-31",
    }, db=None)
    assert_response_shape(result, "compare_periods")
    assert_failure(result)

def test_compare_periods_start_after_end_rejected():
    result = registry.call("compare_periods", {
        "start_date": "2024-01-31", "end_date": "2024-01-01",
        "compare_start": "2023-12-01", "compare_end": "2023-12-31",
    }, db=None)
    assert_failure(result)


# ---------------------------------------------------------------------------
# Input validation — enums and numeric
# ---------------------------------------------------------------------------

def test_subscription_risks_invalid_risk_level():
    result = registry.call("get_subscription_risks", {"risk_level": "unknown_level"}, db=None)
    assert_failure(result)

def test_opportunities_invalid_category():
    result = registry.call("get_opportunities", {"category": "FAKE_CATEGORY"}, db=None)
    assert_failure(result)

def test_payment_failures_limit_out_of_range():
    result = registry.call("get_payment_failures", {"limit": 999}, db=None)
    assert_failure(result)

def test_payment_failures_negative_offset():
    result = registry.call("get_payment_failures", {"offset": -1}, db=None)
    assert_failure(result)

def test_winback_candidates_invalid_days():
    result = registry.call("get_winback_candidates", {"min_days_inactive": -5}, db=None)
    assert_failure(result)

def test_opportunity_details_missing_id():
    result = registry.call("get_opportunity_details", {}, db=None)
    assert_failure(result)

def test_opportunity_details_empty_id():
    result = registry.call("get_opportunity_details", {"opportunity_id": ""}, db=None)
    assert_failure(result)


# ---------------------------------------------------------------------------
# Tool file security: no direct DB imports
# ---------------------------------------------------------------------------

def test_tool_files_do_not_import_db_session():
    tool_dir = pathlib.Path("app/tools")
    forbidden = ["from app.db", "app.db.session", "SessionLocal", "get_db"]
    for py_file in tool_dir.rglob("*.py"):
        source = py_file.read_text()
        for pattern in forbidden:
            assert pattern not in source, (
                f"{py_file} contains forbidden import pattern: '{pattern}'"
            )

def test_tool_implementations_do_not_import_sqlalchemy_directly():
    impl_dir = pathlib.Path("app/tools/implementations")
    for py_file in impl_dir.rglob("*.py"):
        source = py_file.read_text()
        assert "from sqlalchemy" not in source, (
            f"{py_file} imports sqlalchemy directly — use service layer instead"
        )
        assert "import sqlalchemy" not in source, (
            f"{py_file} imports sqlalchemy directly — use service layer instead"
        )


# ---------------------------------------------------------------------------
# Execution tests with real DB (uses existing conftest.py `db` fixture)
# ---------------------------------------------------------------------------

def test_revenue_overview_success(db):
    result = registry.call("get_revenue_overview", {}, db=db)
    assert_response_shape(result, "get_revenue_overview")
    assert_success(result)
    assert "gross_revenue" in result["data"]
    assert "net_revenue" in result["data"]
    assert "order_count" in result["data"]

def test_revenue_overview_with_valid_dates(db):
    result = registry.call("get_revenue_overview", {"start_date": "2020-01-01", "end_date": "2030-12-31"}, db=db)
    assert_success(result)

def test_payment_failures_success(db):
    result = registry.call("get_payment_failures", {}, db=db)
    assert_response_shape(result, "get_payment_failures")
    assert_success(result)
    assert "summary" in result["data"]
    assert "failures" in result["data"]
    assert "pagination" in result["data"]

def test_recoverable_revenue_success(db):
    result = registry.call("get_recoverable_revenue", {}, db=db)
    assert_response_shape(result, "get_recoverable_revenue")
    assert_success(result)
    assert "recoverable" in result["data"]

def test_checkout_metrics_success(db):
    result = registry.call("get_checkout_metrics", {}, db=db)
    assert_response_shape(result, "get_checkout_metrics")
    assert_success(result)
    assert "checkout_starts" in result["data"]
    assert "abandonment_rate" in result["data"]

def test_customer_metrics_success(db):
    result = registry.call("get_customer_metrics", {}, db=db)
    assert_response_shape(result, "get_customer_metrics")
    assert_success(result)
    assert "active_customers" in result["data"]
    assert "total_customers" in result["data"]

def test_winback_candidates_success(db):
    result = registry.call("get_winback_candidates", {"min_days_inactive": 1, "limit": 10}, db=db)
    assert_response_shape(result, "get_winback_candidates")
    assert_success(result)
    assert "candidates" in result["data"]
    assert "count" in result["data"]

def test_subscription_risks_success(db):
    result = registry.call("get_subscription_risks", {}, db=db)
    assert_response_shape(result, "get_subscription_risks")
    assert_success(result)
    assert "at_risk_subscriptions" in result["data"]

def test_subscription_risks_past_due_filter(db):
    result = registry.call("get_subscription_risks", {"risk_level": "past_due"}, db=db)
    assert_success(result)
    assert result["data"]["risk_level_filter"] == "past_due"

def test_refund_metrics_success(db):
    result = registry.call("get_refund_metrics", {}, db=db)
    assert_response_shape(result, "get_refund_metrics")
    assert_success(result)
    assert "refund_count" in result["data"]
    assert "refund_rate" in result["data"]

def test_product_metrics_success(db):
    result = registry.call("get_product_metrics", {}, db=db)
    assert_response_shape(result, "get_product_metrics")
    assert_success(result)
    assert "products" in result["data"]
    assert "total_revenue" in result["data"]

def test_get_opportunities_success(db):
    result = registry.call("get_opportunities", {}, db=db)
    assert_response_shape(result, "get_opportunities")
    assert_success(result)
    assert "opportunities" in result["data"]
    assert "total_estimated_impact" in result["data"]

def test_get_opportunities_category_filter(db):
    result = registry.call("get_opportunities", {"category": "PAYMENT_RECOVERY"}, db=db)
    assert_success(result)
    for opp in result["data"]["opportunities"]:
        assert opp["type"] == "PAYMENT_RECOVERY"

def test_get_opportunity_details_not_found(db):
    result = registry.call("get_opportunity_details", {"opportunity_id": "opp_does_not_exist"}, db=db)
    assert_response_shape(result, "get_opportunity_details")
    assert_failure(result)

def test_compare_periods_success(db):
    result = registry.call("compare_periods", {
        "start_date": "2024-01-01", "end_date": "2024-01-31",
        "compare_start": "2023-12-01", "compare_end": "2023-12-31",
    }, db=db)
    assert_response_shape(result, "compare_periods")
    assert_success(result)
    assert "current_period" in result["data"]
    assert "compare_period" in result["data"]
    assert "changes" in result["data"]
    changes = result["data"]["changes"]
    assert "gross_revenue_pct" in changes
    assert "order_count_pct" in changes

def test_all_tools_return_correct_tool_name(db):
    params_map = {
        "get_revenue_overview": {},
        "get_payment_failures": {},
        "get_recoverable_revenue": {},
        "get_checkout_metrics": {},
        "get_customer_metrics": {},
        "get_winback_candidates": {"min_days_inactive": 1},
        "get_subscription_risks": {},
        "get_refund_metrics": {},
        "get_product_metrics": {},
        "get_opportunities": {},
        "get_opportunity_details": {"opportunity_id": "opp_nonexistent"},
        "compare_periods": {
            "start_date": "2024-01-01", "end_date": "2024-01-31",
            "compare_start": "2023-12-01", "compare_end": "2023-12-31",
        },
    }
    for name, params in params_map.items():
        result = registry.call(name, params, db=db)
        assert result["tool"] == name, f"Tool name mismatch for {name}"
