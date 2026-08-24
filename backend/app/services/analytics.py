from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.merchant import Customer, CustomerSegment, Order, OrderStatus, Payment, PaymentStatus, Product, Refund, Subscription, SubscriptionStatus

MONEY = Decimal("0.01")
RATE = Decimal("0.0001")
DEFAULT_RECOVERY_ASSUMPTION = Decimal("0.25")


def money(value: Any) -> Decimal:
    return (Decimal(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def rate(value: Any) -> Decimal:
    return (Decimal(value or 0)).quantize(RATE, rounding=ROUND_HALF_UP)


def pct_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return rate((current - previous) / previous)


def counts_by(db: Session, column, where=None) -> dict[str, int]:
    stmt = select(column, func.count()).group_by(column)
    if where is not None:
        stmt = stmt.where(where)
    return {str(key): count for key, count in db.execute(stmt).all()}


def sums_by(db: Session, column, amount, where=None) -> dict[str, Decimal]:
    stmt = select(column, func.coalesce(func.sum(amount), 0)).group_by(column)
    if where is not None:
        stmt = stmt.where(where)
    return {str(key): money(total) for key, total in db.execute(stmt).all()}


def revenue_metrics(db: Session) -> dict[str, Any]:
    gross = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED)))
    refunds = money(db.scalar(select(func.coalesce(func.sum(Refund.amount), 0))))
    successful_payment_revenue = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.SUCCEEDED)))
    order_count = db.scalar(select(func.count()).select_from(Order).where(Order.status == OrderStatus.COMPLETED)) or 0
    transaction_count = db.scalar(select(func.count()).select_from(Payment)) or 0
    return {
        "gross_revenue": gross,
        "net_revenue": money(gross - refunds),
        "successful_payment_revenue": successful_payment_revenue,
        "order_count": order_count,
        "aov": money(gross / order_count) if order_count else money(0),
        "transaction_count": transaction_count,
    }


def payments_metrics(db: Session, recovery_assumption: Decimal = DEFAULT_RECOVERY_ASSUMPTION) -> dict[str, Any]:
    total = db.scalar(select(func.count()).select_from(Payment)) or 0
    succeeded = db.scalar(select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.SUCCEEDED)) or 0
    failed = db.scalar(select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.FAILED)) or 0
    failed_value = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.FAILED)))
    eligible_count = db.scalar(select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.FAILED, Payment.retry_eligible.is_(True))) or 0
    eligible_customers = db.scalar(select(func.count(distinct(Payment.customer_id))).where(Payment.status == PaymentStatus.FAILED, Payment.retry_eligible.is_(True))) or 0
    eligible_value = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.FAILED, Payment.retry_eligible.is_(True))))
    repeated = db.scalar(select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.FAILED, Payment.retry_count > 0)) or 0
    retry_eligible = db.scalar(select(func.count()).select_from(Payment).where(Payment.retry_eligible.is_(True))) or 0
    return {
        "success_rate": rate(Decimal(succeeded) / Decimal(total)) if total else rate(0),
        "failure_rate": rate(Decimal(failed) / Decimal(total)) if total else rate(0),
        "failed_payment_value": failed_value,
        "failure_reasons": sums_by(db, Payment.failure_reason, Payment.amount, Payment.status == PaymentStatus.FAILED),
        "payment_method_breakdown": sums_by(db, Payment.payment_method, Payment.amount),
        "repeated_failures": repeated,
        "retry_eligibility": {"eligible": retry_eligible, "ineligible": total - retry_eligible},
        "recoverable_revenue": {
            "eligible_payment_count": eligible_count,
            "eligible_customer_count": eligible_customers,
            "failed_value": eligible_value,
            "recovery_assumption": rate(recovery_assumption),
            "estimated_recoverable_revenue": money(eligible_value * recovery_assumption),
        },
    }


def checkout_metrics(db: Session) -> dict[str, Any]:
    starts = db.scalar(select(func.count()).select_from(Order)) or 0
    completed = db.scalar(select(func.count()).select_from(Order).where(Order.checkout_completed_at.is_not(None))) or 0
    abandoned = db.scalar(select(func.count()).select_from(Order).where(Order.status == OrderStatus.ABANDONED)) or 0
    abandoned_value = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.ABANDONED)))
    rows = db.execute(select(Product.name, func.count(Order.id), func.coalesce(func.sum(Order.amount), 0)).join(Order).where(Order.status == OrderStatus.ABANDONED).group_by(Product.name)).all()
    return {"checkout_starts": starts, "completed_checkouts": completed, "abandoned_checkouts": abandoned, "abandonment_rate": rate(Decimal(abandoned) / Decimal(starts)) if starts else rate(0), "abandoned_value": abandoned_value, "product_level_abandonment": {name: {"count": count, "value": money(value)} for name, count, value in rows}}


def customers_metrics(db: Session, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    inactive_cutoff = now - timedelta(days=90)
    active = db.scalar(select(func.count()).select_from(Customer).where(Customer.last_purchase_date >= inactive_cutoff)) or 0
    inactive = db.scalar(select(func.count()).select_from(Customer).where((Customer.last_purchase_date < inactive_cutoff) | (Customer.last_purchase_date.is_(None)))) or 0
    repeat = db.scalar(select(func.count()).select_from(select(Order.customer_id).where(Order.status == OrderStatus.COMPLETED).group_by(Order.customer_id).having(func.count(Order.id) > 1).subquery())) or 0
    high_value = db.scalar(select(func.count()).select_from(Customer).where((Customer.segment == CustomerSegment.HIGH_VALUE) | (Customer.total_spend >= 2500))) or 0
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    gross = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED)))
    orders = db.scalar(select(func.count()).select_from(Order).where(Order.status == OrderStatus.COMPLETED)) or 0
    avg_frequency = rate(db.scalar(select(func.coalesce(func.avg(Customer.purchase_frequency), 0))))
    days_rows = db.execute(select(Customer.id, Customer.last_purchase_date).where(Customer.last_purchase_date.is_not(None))).all()
    avg_days = rate(sum(Decimal((now.replace(tzinfo=None) - dt.replace(tzinfo=None)).days) for _, dt in days_rows) / Decimal(len(days_rows))) if days_rows else rate(0)
    win_back = db.scalar(select(func.count()).select_from(Customer).where((Customer.segment.in_([CustomerSegment.AT_RISK, CustomerSegment.INACTIVE])) | (Customer.churn_probability >= Decimal("0.5")))) or 0
    return {"active_customers": active, "inactive_customers": inactive, "repeat_customers": repeat, "high_value_customers": high_value, "purchase_frequency": avg_frequency, "aov": money(gross / orders) if orders else money(0), "days_since_last_purchase": avg_days, "win_back_signals": win_back, "total_customers": total_customers}


def subscriptions_metrics(db: Session) -> dict[str, Any]:
    active = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE)) or 0
    cancelled = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == SubscriptionStatus.CANCELLED)) or 0
    past_due = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == SubscriptionStatus.PAST_DUE)) or 0
    failed_recurring = db.scalar(select(func.coalesce(func.sum(Subscription.failed_attempts), 0))) or 0
    revenue = money(db.scalar(select(func.coalesce(func.sum(Subscription.amount), 0)).where(Subscription.status == SubscriptionStatus.ACTIVE)))
    risk = db.scalar(select(func.count()).select_from(Subscription).where((Subscription.status == SubscriptionStatus.PAST_DUE) | (Subscription.failed_attempts > 0))) or 0
    return {"active": active, "cancelled": cancelled, "past_due": past_due, "failed_recurring_payments": failed_recurring, "subscription_revenue": revenue, "retention_risk": risk}


def refunds_metrics(db: Session) -> dict[str, Any]:
    count = db.scalar(select(func.count()).select_from(Refund)) or 0
    value = money(db.scalar(select(func.coalesce(func.sum(Refund.amount), 0))))
    gross = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED)))
    product_rows = db.execute(select(Product.name, func.count(Refund.id), func.coalesce(func.sum(Refund.amount), 0)).join(Order).join(Payment).join(Refund).group_by(Product.name)).all()
    return {"refund_count": count, "refund_value": value, "refund_rate": rate(value / gross) if gross else rate(0), "product_refund_concentration": {n: {"count": c, "value": money(v)} for n, c, v in product_rows}, "refund_reasons": sums_by(db, Refund.reason, Refund.amount)}


def trends_metrics(db: Session, now: datetime | None = None) -> dict[str, Any]:
    now = now or (db.scalar(select(func.max(Order.created_at))) or datetime.now(UTC))
    current_start = now - timedelta(days=7)
    previous_start = now - timedelta(days=14)
    current = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED, Order.created_at >= current_start, Order.created_at <= now)))
    previous = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED, Order.created_at >= previous_start, Order.created_at < current_start)))
    daily_rows = db.execute(select(func.date(Order.created_at), func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at))).all()
    daily = {str(k): money(v) for k, v in daily_rows}
    weekly: dict[str, Decimal] = {}
    for day, value in daily.items():
        year, week, _ = datetime.fromisoformat(day).isocalendar()
        key = f"{year}-W{week:02d}"
        weekly[key] = money(weekly.get(key, Decimal(0)) + value)
    return {"daily": daily, "weekly": weekly, "previous_period_comparison": {"current_period_revenue": current, "previous_period_revenue": previous, "percentage_change": pct_change(current, previous)}}


def overview(db: Session, recovery_assumption: Decimal = DEFAULT_RECOVERY_ASSUMPTION) -> dict[str, Any]:
    return {"revenue": revenue_metrics(db), "payments": payments_metrics(db, recovery_assumption), "checkout": checkout_metrics(db), "customers": customers_metrics(db), "subscriptions": subscriptions_metrics(db), "refunds": refunds_metrics(db), "trends": trends_metrics(db)}
