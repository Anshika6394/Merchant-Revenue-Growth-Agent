"""Phase 5 – Pydantic v2 input schemas for all 12 tools."""
from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DateRangeMixin(BaseModel):
    start_date: str | None = Field(None, description="Start date YYYY-MM-DD")
    end_date: str | None = Field(None, description="End date YYYY-MM-DD")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _validate_date_fmt(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            date.fromisoformat(str(v))
        except ValueError:
            raise ValueError(f"Invalid date '{v}'. Use YYYY-MM-DD format.")
        return str(v)

    @model_validator(mode="after")
    def _validate_order(self) -> "DateRangeMixin":
        if self.start_date and self.end_date:
            if date.fromisoformat(self.start_date) > date.fromisoformat(self.end_date):
                raise ValueError("start_date must not be after end_date.")
        return self

    def start(self) -> date | None:
        return date.fromisoformat(self.start_date) if self.start_date else None

    def end(self) -> date | None:
        return date.fromisoformat(self.end_date) if self.end_date else None


class RevenueOverviewInput(DateRangeMixin):
    """Inputs for get_revenue_overview."""


class PaymentFailuresInput(DateRangeMixin):
    """Inputs for get_payment_failures."""
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class RecoverableRevenueInput(BaseModel):
    """Inputs for get_recoverable_revenue — no date filter needed."""


class CheckoutMetricsInput(DateRangeMixin):
    """Inputs for get_checkout_metrics."""


class CustomerMetricsInput(DateRangeMixin):
    """Inputs for get_customer_metrics."""


class WinbackCandidatesInput(BaseModel):
    """Inputs for get_winback_candidates."""
    min_days_inactive: int = Field(90, ge=1, le=3650)
    limit: int = Field(50, ge=1, le=200)


class SubscriptionRisksInput(BaseModel):
    """Inputs for get_subscription_risks."""
    risk_level: Literal["all", "past_due", "failed"] = Field("all")
    limit: int = Field(50, ge=1, le=200)


class RefundMetricsInput(DateRangeMixin):
    """Inputs for get_refund_metrics."""


class ProductMetricsInput(DateRangeMixin):
    """Inputs for get_product_metrics."""
    product_name: str | None = Field(None, max_length=200)


class GetOpportunitiesInput(BaseModel):
    """Inputs for get_opportunities."""
    category: Literal[
        "all", "PAYMENT_RECOVERY", "CHECKOUT_RECOVERY",
        "CUSTOMER_WINBACK", "SUBSCRIPTION_RETENTION",
        "REFUND_LEAKAGE", "PRODUCT_GROWTH",
    ] = Field("all")
    min_impact: float | None = Field(None, ge=0)


class OpportunityDetailsInput(BaseModel):
    """Inputs for get_opportunity_details."""
    opportunity_id: str = Field(..., min_length=1, max_length=100)


class ComparePeriodsInput(BaseModel):
    """Inputs for compare_periods."""
    start_date: str = Field(..., description="Current period start YYYY-MM-DD")
    end_date: str = Field(..., description="Current period end YYYY-MM-DD")
    compare_start: str = Field(..., description="Comparison period start YYYY-MM-DD")
    compare_end: str = Field(..., description="Comparison period end YYYY-MM-DD")

    @field_validator("start_date", "end_date", "compare_start", "compare_end", mode="before")
    @classmethod
    def _validate_date_fmt(cls, v: Any) -> Any:
        try:
            date.fromisoformat(str(v))
        except ValueError:
            raise ValueError(f"Invalid date '{v}'. Use YYYY-MM-DD format.")
        return str(v)

    @model_validator(mode="after")
    def _validate_ranges(self) -> "ComparePeriodsInput":
        if date.fromisoformat(self.start_date) > date.fromisoformat(self.end_date):
            raise ValueError("start_date must not be after end_date.")
        if date.fromisoformat(self.compare_start) > date.fromisoformat(self.compare_end):
            raise ValueError("compare_start must not be after compare_end.")
        return self

    def start(self) -> date:
        return date.fromisoformat(self.start_date)

    def end(self) -> date:
        return date.fromisoformat(self.end_date)

    def cmp_start(self) -> date:
        return date.fromisoformat(self.compare_start)

    def cmp_end(self) -> date:
        return date.fromisoformat(self.compare_end)
