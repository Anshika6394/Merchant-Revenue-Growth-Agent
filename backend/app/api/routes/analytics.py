from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, get_current_user
from app.models.user import User
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])
CurrentUser = Annotated[User, Depends(get_current_user)]
RecoveryAssumption = Annotated[Decimal, Query(ge=0, le=1, description="Expected recovery rate for retry-eligible failed payments.")]


@router.get("/overview")
def overview(db: DbSession, current_user: CurrentUser, recovery_assumption: RecoveryAssumption = analytics.DEFAULT_RECOVERY_ASSUMPTION) -> dict[str, Any]:
    return analytics.overview(db, recovery_assumption)


@router.get("/revenue")
def revenue(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    return analytics.revenue_metrics(db)


@router.get("/payments")
def payments(db: DbSession, current_user: CurrentUser, recovery_assumption: RecoveryAssumption = analytics.DEFAULT_RECOVERY_ASSUMPTION) -> dict[str, Any]:
    return analytics.payments_metrics(db, recovery_assumption)


@router.get("/checkout")
def checkout(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    return analytics.checkout_metrics(db)


@router.get("/customers")
def customers(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    return analytics.customers_metrics(db)


@router.get("/subscriptions")
def subscriptions(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    return analytics.subscriptions_metrics(db)


@router.get("/refunds")
def refunds(db: DbSession, current_user: CurrentUser) -> dict[str, Any]:
    return analytics.refunds_metrics(db)
