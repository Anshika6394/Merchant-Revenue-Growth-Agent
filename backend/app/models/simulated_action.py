"""Phase 10 - Action Simulation Model."""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid, enum
from app.db.session import Base

class ActionType(str, enum.Enum):
    RETRY_PAYMENT = "retry_payment"
    CHECKOUT_RECOVERY = "checkout_recovery"
    WINBACK_CAMPAIGN = "winback_campaign"
    SUBSCRIPTION_RETENTION = "subscription_retention"
    PRODUCT_PROMOTION = "product_promotion"

class ActionStatus(str, enum.Enum):
    RECOMMENDED = "recommended"
    SIMULATED = "simulated"
    SUCCESSFUL = "successful"
    UNSUCCESSFUL = "unsuccessful"
    DISMISSED = "dismissed"

class SimulatedAction(Base):
    __tablename__ = "simulated_actions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id = Column(String, ForeignKey("opportunities.id"), nullable=True)
    action_type = Column(String, nullable=False)
    target_count = Column(Integer, default=0)
    estimated_cost = Column(Numeric(12, 2), default=0)
    estimated_revenue = Column(Numeric(12, 2), default=0)
    expected_conversion = Column(Numeric(5, 4), default=0)
    status = Column(String, default=ActionStatus.SIMULATED)
    simulation_result = Column(String, nullable=True)
    feedback = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
