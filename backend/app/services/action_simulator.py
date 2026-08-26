"""Phase 10 - Action Simulator Service."""
from __future__ import annotations
from decimal import Decimal
from typing import Any
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.simulated_action import SimulatedAction, ActionType, ActionStatus

CONVERSION_RATES = {
    ActionType.RETRY_PAYMENT: Decimal("0.28"),
    ActionType.CHECKOUT_RECOVERY: Decimal("0.22"),
    ActionType.WINBACK_CAMPAIGN: Decimal("0.18"),
    ActionType.SUBSCRIPTION_RETENTION: Decimal("0.65"),
    ActionType.PRODUCT_PROMOTION: Decimal("0.15"),
}

COST_PER_TARGET = {
    ActionType.RETRY_PAYMENT: Decimal("5"),
    ActionType.CHECKOUT_RECOVERY: Decimal("8"),
    ActionType.WINBACK_CAMPAIGN: Decimal("12"),
    ActionType.SUBSCRIPTION_RETENTION: Decimal("10"),
    ActionType.PRODUCT_PROMOTION: Decimal("15"),
}

def simulate_action(
    db: Session,
    opportunity_id: str | None,
    action_type: str,
    target_count: int,
    avg_value: float,
) -> dict[str, Any]:
    atype = ActionType(action_type)
    conversion = CONVERSION_RATES.get(atype, Decimal("0.20"))
    cost_per = COST_PER_TARGET.get(atype, Decimal("10"))
    avg = Decimal(str(avg_value))
    estimated_converted = int(target_count * float(conversion))
    estimated_revenue = avg * estimated_converted
    estimated_cost = cost_per * target_count
    roi = float((estimated_revenue - estimated_cost) / estimated_cost * 100) if estimated_cost else 0

    result_text = (
        f"[SIMULATED] Targeting {target_count} customers. "
        f"Expected conversion: {float(conversion)*100:.0f}%. "
        f"Estimated conversions: {estimated_converted}. "
        f"Estimated recovered revenue: INR {float(estimated_revenue):,.0f}. "
        f"Campaign cost: INR {float(estimated_cost):,.0f}. "
        f"Expected ROI: {roi:.1f}%."
    )

    action = SimulatedAction(
        id=str(uuid.uuid4()),
        opportunity_id=opportunity_id,
        action_type=action_type,
        target_count=target_count,
        estimated_cost=estimated_cost,
        estimated_revenue=estimated_revenue,
        expected_conversion=conversion,
        status=ActionStatus.SIMULATED,
        simulation_result=result_text,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return {
        "action_id": action.id,
        "opportunity_id": opportunity_id,
        "action_type": action_type,
        "target_count": target_count,
        "estimated_cost": float(estimated_cost),
        "estimated_revenue": float(estimated_revenue),
        "expected_conversion": float(conversion),
        "estimated_conversions": estimated_converted,
        "roi_percent": round(roi, 1),
        "status": ActionStatus.SIMULATED,
        "simulation_result": result_text,
        "label": "SIMULATED",
    }

def get_actions(db: Session) -> list[dict]:
    actions = db.query(SimulatedAction).order_by(SimulatedAction.created_at.desc()).all()
    return [_to_dict(a) for a in actions]

def submit_feedback(db: Session, action_id: str, feedback: str, status: str) -> dict:
    action = db.query(SimulatedAction).filter(SimulatedAction.id == action_id).first()
    if not action:
        return {"error": "Action not found"}
    action.feedback = feedback
    action.status = status
    action.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(action)
    return _to_dict(action)

def _to_dict(a: SimulatedAction) -> dict:
    return {
        "action_id": a.id,
        "opportunity_id": a.opportunity_id,
        "action_type": a.action_type,
        "target_count": a.target_count,
        "estimated_cost": float(a.estimated_cost or 0),
        "estimated_revenue": float(a.estimated_revenue or 0),
        "expected_conversion": float(a.expected_conversion or 0),
        "status": a.status,
        "simulation_result": a.simulation_result,
        "feedback": a.feedback,
        "created_at": str(a.created_at),
        "label": "SIMULATED",
    }
