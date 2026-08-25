"""Phase 5 – Tool Layer base utilities. No DB imports allowed here."""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

_SENSITIVE = (
    "password", "secret_key", "jwt_secret", "database_url", "db_url",
    "api_key", "private_key", "sqlalchemy", "traceback", "sessionlocal",
    "os.environ", "settings.",
)


def _default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Not JSON serializable: {type(obj).__name__}")


def serialize_data(data: Any) -> Any:
    """Recursively convert Decimal → float for JSON safety."""
    return json.loads(json.dumps(data, default=_default))


def sanitize_error(raw: str) -> str:
    """Strip sensitive substrings from error messages."""
    lower = raw.lower()
    for pattern in _SENSITIVE:
        if pattern in lower:
            return "An internal error occurred. Please try again."
    return raw


def success_result(tool: str, data: Any, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "success": True,
        "tool": tool,
        "data": serialize_data(data),
        "evidence": serialize_data(evidence),
        "error": None,
    }


def error_result(tool: str, message: str) -> dict[str, Any]:
    return {
        "success": False,
        "tool": tool,
        "data": {},
        "evidence": [],
        "error": sanitize_error(message),
    }
