"""Opportunity service wrapping existing tools."""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from app.models.merchant import Opportunity
from app.tools.implementations.opportunity_tools import get_opportunities as _get_opps, get_opportunity_details
from app.agents.payment_recovery_agent import PaymentRecoveryAgent
from app.agents.checkout_recovery_agent import CheckoutRecoveryAgent
from app.agents.winback_agent import WinbackAgent
from app.agents.subscription_retention_agent import SubscriptionRetentionAgent
from app.agents.revenue_leakage_agent import RevenueLeakageAgent
from app.agents.product_growth_agent import ProductGrowthAgent
from app.tools.registry import registry

def get_opportunities(db: Session) -> list[dict]:
    result = _get_opps(db, {})
    return result.get("data", {}).get("opportunities", [])

def get_opportunity(db: Session, opportunity_id: str) -> dict:
    result = get_opportunity_details(db, {"opportunity_id": opportunity_id})
    return result.get("data", {})

def detect_opportunities(db: Session) -> dict:
    agents = [
        PaymentRecoveryAgent(registry),
        CheckoutRecoveryAgent(registry),
        WinbackAgent(registry),
        SubscriptionRetentionAgent(registry),
        RevenueLeakageAgent(registry),
        ProductGrowthAgent(registry),
    ]
    results = []
    for agent in agents:
        try:
            r = agent.analyze(db=db)
            if r:
                results.append(r)
        except Exception as e:
            results.append({"error": str(e), "agent": agent.__class__.__name__})
    return {"detected": len(results), "opportunities": results}
