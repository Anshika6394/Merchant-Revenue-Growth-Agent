"""
Phase 5 – Tool Analytics Service.

Date-aware analytics wrappers for the Tool Layer.
Tools call THIS module — never the database directly.
This module is a SERVICE (uses SQLAlchemy Session) — it is NOT a tool.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.merchant import (
    Customer,
    CustomerSegment,
    Order,
    OrderStatus,
    Payment,
    PaymentStatus,
    Product,
    Refund,
    Subscription,
    SubscriptionStatus,
)
from app.services.analytics import (
    DEFAULT_RECOVERY_ASSUMPTION,
    checkout_metrics as _checkout_all,
    customers_metrics,
    money,
    payments_metrics,
    rate,
    refunds_metrics as _refunds_all,
    subscriptions_metrics,
)


def _dt_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 0, 0, 0)


def _dt_end(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, 23, 59, 59)


# ---------------------------------------------------------------------------
# Revenue
# ---------------------------------------------------------------------------

def revenue_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    o_conds = [Order.status == OrderStatus.COMPLETED]
    p_conds = [Payment.status == PaymentStatus.SUCCEEDED]
    r_conds: list = []
    if start:
        o_conds.append(Order.created_at >= _dt_start(start))
        p_conds.append(Payment.created_at >= _dt_start(start))
        r_conds.append(Refund.created_at >= _dt_start(start))
    if end:
        o_conds.append(Order.created_at <= _dt_end(end))
        p_conds.append(Payment.created_at <= _dt_end(end))
        r_conds.append(Refund.created_at <= _dt_end(end))

    gross = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(*o_conds)))
    pay_gross = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(*p_conds)))
    ref_stmt = select(func.coalesce(func.sum(Refund.amount), 0))
    if r_conds:
        ref_stmt = ref_stmt.where(*r_conds)
    refunds_total = money(db.scalar(ref_stmt))
    order_count = db.scalar(select(func.count()).select_from(Order).where(*o_conds)) or 0

    return {
        "gross_revenue": gross,
        "net_revenue": money(gross - refunds_total),
        "successful_payment_revenue": pay_gross,
        "refunds_total": refunds_total,
        "order_count": order_count,
        "aov": money(gross / order_count) if order_count else money(0),
        "date_range": {
            "start": str(start) if start else "all-time",
            "end": str(end) if end else "all-time",
        },
    }


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

def payments_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    base: list = []
    if start:
        base.append(Payment.created_at >= _dt_start(start))
    if end:
        base.append(Payment.created_at <= _dt_end(end))

    failed_c = list(base) + [Payment.status == PaymentStatus.FAILED]
    succ_c = list(base) + [Payment.status == PaymentStatus.SUCCEEDED]
    elig_c = list(failed_c) + [Payment.retry_eligible.is_(True)]

    total = db.scalar(
        select(func.count()).select_from(Payment).where(*base) if base
        else select(func.count()).select_from(Payment)
    ) or 0
    failed = db.scalar(select(func.count()).select_from(Payment).where(*failed_c)) or 0
    succeeded = db.scalar(select(func.count()).select_from(Payment).where(*succ_c)) or 0
    failed_val = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(*failed_c)))
    elig_count = db.scalar(select(func.count()).select_from(Payment).where(*elig_c)) or 0
    elig_val = money(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(*elig_c)))
    elig_cust = db.scalar(select(func.count(distinct(Payment.customer_id))).where(*elig_c)) or 0

    rows = db.execute(
        select(Payment).where(*failed_c).offset(offset).limit(limit)
    ).scalars().all()

    failures = [
        {
            "payment_id": str(p.id),
            "customer_id": str(p.customer_id),
            "amount": money(p.amount),
            "failure_reason": str(p.failure_reason) if p.failure_reason else None,
            "payment_method": str(p.payment_method) if p.payment_method else None,
            "retry_eligible": bool(p.retry_eligible),
            "retry_count": int(p.retry_count or 0),
        }
        for p in rows
    ]

    ra = DEFAULT_RECOVERY_ASSUMPTION
    return {
        "summary": {
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": rate(Decimal(succeeded) / Decimal(total)) if total else rate(0),
            "failure_rate": rate(Decimal(failed) / Decimal(total)) if total else rate(0),
            "failed_value": failed_val,
        },
        "failures": failures,
        "pagination": {"limit": limit, "offset": offset, "total_failures": failed},
        "recoverable": {
            "eligible_payment_count": elig_count,
            "eligible_customer_count": elig_cust,
            "failed_value": elig_val,
            "recovery_assumption": rate(ra),
            "estimated_recoverable_revenue": money(elig_val * ra),
        },
        "date_range": {
            "start": str(start) if start else "all-time",
            "end": str(end) if end else "all-time",
        },
    }


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

def checkout_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    if not start and not end:
        result = _checkout_all(db)
        result["date_range"] = {"start": "all-time", "end": "all-time"}
        return result

    base: list = []
    if start:
        base.append(Order.created_at >= _dt_start(start))
    if end:
        base.append(Order.created_at <= _dt_end(end))

    aband = list(base) + [Order.status == OrderStatus.ABANDONED]
    compl = list(base) + [Order.checkout_completed_at.is_not(None)]

    starts = db.scalar(select(func.count()).select_from(Order).where(*base) if base else select(func.count()).select_from(Order)) or 0
    completed = db.scalar(select(func.count()).select_from(Order).where(*compl)) or 0
    abandoned = db.scalar(select(func.count()).select_from(Order).where(*aband)) or 0
    ab_val = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(*aband)))
    prod_rows = db.execute(
        select(Product.name, func.count(Order.id), func.coalesce(func.sum(Order.amount), 0))
        .join(Order).where(*aband).group_by(Product.name)
    ).all()

    return {
        "checkout_starts": starts,
        "completed_checkouts": completed,
        "abandoned_checkouts": abandoned,
        "abandonment_rate": rate(Decimal(abandoned) / Decimal(starts)) if starts else rate(0),
        "abandoned_value": ab_val,
        "product_level_abandonment": {n: {"count": c, "value": money(v)} for n, c, v in prod_rows},
        "date_range": {"start": str(start), "end": str(end)},
    }


# ---------------------------------------------------------------------------
# Refunds
# ---------------------------------------------------------------------------

def refunds_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    if not start and not end:
        result = _refunds_all(db)
        result["date_range"] = {"start": "all-time", "end": "all-time"}
        return result

    conds: list = []
    if start:
        conds.append(Refund.created_at >= _dt_start(start))
    if end:
        conds.append(Refund.created_at <= _dt_end(end))

    count = db.scalar(select(func.count()).select_from(Refund).where(*conds)) or 0
    value = money(db.scalar(select(func.coalesce(func.sum(Refund.amount), 0)).where(*conds)))
    gross = money(db.scalar(select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.COMPLETED)))
    reasons = {
        str(r): money(v)
        for r, v in db.execute(
            select(Refund.reason, func.coalesce(func.sum(Refund.amount), 0))
            .where(*conds).group_by(Refund.reason)
        ).all()
    }

    return {
        "refund_count": count,
        "refund_value": value,
        "refund_rate": rate(value / gross) if gross else rate(0),
        "refund_reasons": reasons,
        "date_range": {"start": str(start), "end": str(end)},
    }


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def products_for_period(
    db: Session,
    start: date | None = None,
    end: date | None = None,
    product_name: str | None = None,
) -> dict[str, Any]:
    conds = [Order.status == OrderStatus.COMPLETED]
    if start:
        conds.append(Order.created_at >= _dt_start(start))
    if end:
        conds.append(Order.created_at <= _dt_end(end))

    stmt = (
        select(Product.name, func.count(Order.id), func.coalesce(func.sum(Order.amount), 0))
        .join(Order).where(*conds).group_by(Product.name)
        .order_by(func.coalesce(func.sum(Order.amount), 0).desc())
    )
    if product_name:
        stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))

    rows = db.execute(stmt).all()
    products = [{"name": n, "order_count": c, "revenue": money(r)} for n, c, r in rows]
    total_rev = sum(money(r) for _, _, r in rows)

    return {
        "products": products,
        "total_products": len(products),
        "total_revenue": total_rev,
        "date_range": {"start": str(start) if start else "all-time", "end": str(end) if end else "all-time"},
    }


# ---------------------------------------------------------------------------
# Winback candidates
# ---------------------------------------------------------------------------

def winback_candidates_list(
    db: Session,
    min_days_inactive: int = 90,
    limit: int = 50,
) -> dict[str, Any]:
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=min_days_inactive)
    rows = db.execute(
        select(Customer)
        .where(
            (Customer.last_purchase_date < cutoff) | Customer.last_purchase_date.is_(None),
            Customer.segment.in_([CustomerSegment.AT_RISK, CustomerSegment.INACTIVE])
            | (Customer.churn_probability >= Decimal("0.5")),
        )
        .order_by(Customer.total_spend.desc())
        .limit(limit)
    ).scalars().all()

    now = datetime.now().replace(tzinfo=None)
    candidates = []
    for c in rows:
        lp = c.last_purchase_date
        if lp and hasattr(lp, "tzinfo") and lp.tzinfo:
            lp = lp.replace(tzinfo=None)
        candidates.append({
            "customer_id": str(c.id),
            "segment": str(c.segment),
            "total_spend": money(c.total_spend),
            "churn_probability": rate(c.churn_probability),
            "last_purchase_date": str(c.last_purchase_date) if c.last_purchase_date else None,
            "days_inactive": int((now - lp).days) if lp else None,
            "purchase_frequency": rate(c.purchase_frequency),
        })

    return {
        "candidates": candidates,
        "count": len(candidates),
        "min_days_inactive": min_days_inactive,
        "total_spend_at_risk": sum(money(c.total_spend) for c in rows),
    }


# ---------------------------------------------------------------------------
# Subscription risks
# ---------------------------------------------------------------------------

def subscription_risks_list(
    db: Session,
    risk_level: str = "all",
    limit: int = 50,
) -> dict[str, Any]:
    if risk_level == "past_due":
        cond = Subscription.status == SubscriptionStatus.PAST_DUE
    elif risk_level == "failed":
        cond = Subscription.failed_attempts > 0
    else:
        cond = (Subscription.status == SubscriptionStatus.PAST_DUE) | (Subscription.failed_attempts > 0)

    rows = db.execute(
        select(Subscription).where(cond).order_by(Subscription.amount.desc()).limit(limit)
    ).scalars().all()

    return {
        "at_risk_subscriptions": [
            {
                "subscription_id": str(s.id),
                "customer_id": str(s.customer_id),
                "status": str(s.status),
                "amount": money(s.amount),
                "failed_attempts": int(s.failed_attempts or 0),
            }
            for s in rows
        ],
        "count": len(rows),
        "total_at_risk_mrr": sum(money(s.amount) for s in rows),
        "risk_level_filter": risk_level,
    }


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

def compute_opportunities(db: Session) -> list[dict[str, Any]]:
    """Deterministic opportunity detection from Phase 3 analytics."""
    opps: list[dict[str, Any]] = []

    # 1. PAYMENT_RECOVERY
    pay = payments_metrics(db)
    rec = pay.get("recoverable_revenue", {})
    elig = int(rec.get("eligible_payment_count", 0))
    if elig > 0:
        opps.append({
            "opportunity_id": "opp_payment_recovery",
            "type": "PAYMENT_RECOVERY",
            "title": "Recover Failed Payments",
            "description": f"{elig} retry-eligible payments can be recovered.",
            "priority": "HIGH" if elig >= 5 else "MEDIUM",
            "estimated_revenue_impact": money(rec.get("estimated_recoverable_revenue", 0)),
            "confidence": rate(Decimal("0.70")),
            "evidence": {
                "eligible_payment_count": elig,
                "eligible_customer_count": rec.get("eligible_customer_count", 0),
                "failed_value": rec.get("failed_value", money(0)),
                "recovery_assumption": str(rec.get("recovery_assumption", "0.25")),
            },
            "status": "open",
        })

    # 2. CHECKOUT_RECOVERY
    ck = _checkout_all(db)
    ab_rate = float(ck.get("abandonment_rate", 0))
    ab_val = money(ck.get("abandoned_value", 0))
    if ab_rate > 0.1:
        opps.append({
            "opportunity_id": "opp_checkout_recovery",
            "type": "CHECKOUT_RECOVERY",
            "title": "Recover Abandoned Checkouts",
            "description": f"Checkout abandonment is {ab_rate * 100:.1f}%.",
            "priority": "HIGH" if ab_rate > 0.3 else "MEDIUM",
            "estimated_revenue_impact": money(ab_val * Decimal("0.20")),
            "confidence": rate(Decimal("0.60")),
            "evidence": {"abandonment_rate": ab_rate, "abandoned_checkouts": ck.get("abandoned_checkouts", 0), "abandoned_value": ab_val},
            "status": "open",
        })

    # 3. CUSTOMER_WINBACK
    cust = customers_metrics(db)
    wb = int(cust.get("win_back_signals", 0))
    aov = money(cust.get("aov", 0))
    if wb > 0:
        opps.append({
            "opportunity_id": "opp_customer_winback",
            "type": "CUSTOMER_WINBACK",
            "title": "Win Back At-Risk Customers",
            "description": f"{wb} customers show churn signals.",
            "priority": "HIGH" if wb >= 10 else "MEDIUM",
            "estimated_revenue_impact": money(Decimal(wb) * aov),
            "confidence": rate(Decimal("0.50")),
            "evidence": {"win_back_signals": wb, "inactive_customers": cust.get("inactive_customers", 0), "aov": aov},
            "status": "open",
        })

    # 4. SUBSCRIPTION_RETENTION
    sub = subscriptions_metrics(db)
    risk = int(sub.get("retention_risk", 0))
    sub_rev = money(sub.get("subscription_revenue", 0))
    if risk > 0:
        opps.append({
            "opportunity_id": "opp_subscription_retention",
            "type": "SUBSCRIPTION_RETENTION",
            "title": "Retain At-Risk Subscriptions",
            "description": f"{risk} subscriptions at churn risk.",
            "priority": "CRITICAL" if risk >= 5 else "HIGH",
            "estimated_revenue_impact": money(sub_rev * Decimal("0.10")),
            "confidence": rate(Decimal("0.80")),
            "evidence": {"retention_risk": risk, "past_due": sub.get("past_due", 0), "failed_recurring_payments": sub.get("failed_recurring_payments", 0), "subscription_revenue": sub_rev},
            "status": "open",
        })

    # 5. REFUND_LEAKAGE
    ref = _refunds_all(db)
    ref_rate = float(ref.get("refund_rate", 0))
    ref_val = money(ref.get("refund_value", 0))
    if ref_rate > 0.03:
        opps.append({
            "opportunity_id": "opp_refund_leakage",
            "type": "REFUND_LEAKAGE",
            "title": "Investigate Refund Concentration",
            "description": f"Refund rate is {ref_rate * 100:.2f}%.",
            "priority": "HIGH" if ref_rate > 0.08 else "MEDIUM",
            "estimated_revenue_impact": ref_val,
            "confidence": rate(Decimal("0.90")),
            "evidence": {"refund_count": ref.get("refund_count", 0), "refund_value": ref_val, "refund_rate": ref_rate},
            "status": "open",
        })

    # 6. PRODUCT_GROWTH
    prod_aband = ck.get("product_level_abandonment", {})
    if prod_aband:
        top = max(prod_aband.items(), key=lambda x: float(x[1].get("value", 0)))
        opps.append({
            "opportunity_id": "opp_product_growth",
            "type": "PRODUCT_GROWTH",
            "title": f"Optimise '{top[0]}' Conversion",
            "description": f"Product '{top[0]}' has the highest abandonment value.",
            "priority": "MEDIUM",
            "estimated_revenue_impact": money(Decimal(str(float(top[1].get("value", 0)))) * Decimal("0.15")),
            "confidence": rate(Decimal("0.50")),
            "evidence": {"product": top[0], "abandonment_count": top[1].get("count", 0), "abandonment_value": top[1].get("value", money(0))},
            "status": "open",
        })

    opps.sort(key=lambda o: float(o.get("estimated_revenue_impact", 0)), reverse=True)
    return opps


def get_opportunity_by_id(db: Session, opp_id: str) -> dict[str, Any] | None:
    for opp in compute_opportunities(db):
        if opp.get("opportunity_id") == opp_id:
            return opp
    return None
