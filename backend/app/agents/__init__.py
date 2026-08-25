"""Phase 6 - Specialized Revenue Growth Agents."""
from app.agents.base_agent import BaseRevenueAgent, build_agent_output, fallback_output, insufficient_evidence_output
from app.agents.payment_recovery_agent import PaymentRecoveryAgent
from app.agents.checkout_recovery_agent import CheckoutRecoveryAgent
from app.agents.winback_agent import WinbackAgent
from app.agents.subscription_retention_agent import SubscriptionRetentionAgent
from app.agents.revenue_leakage_agent import RevenueLeakageAgent
from app.agents.product_growth_agent import ProductGrowthAgent

ALL_AGENTS = [
    PaymentRecoveryAgent,
    CheckoutRecoveryAgent,
    WinbackAgent,
    SubscriptionRetentionAgent,
    RevenueLeakageAgent,
    ProductGrowthAgent,
]

__all__ = [
    "BaseRevenueAgent",
    "build_agent_output",
    "fallback_output",
    "insufficient_evidence_output",
    "PaymentRecoveryAgent",
    "CheckoutRecoveryAgent",
    "WinbackAgent",
    "SubscriptionRetentionAgent",
    "RevenueLeakageAgent",
    "ProductGrowthAgent",
    "ALL_AGENTS",
]
