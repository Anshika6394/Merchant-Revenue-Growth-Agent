"""Deterministic synthetic merchant data for local development only."""
import argparse
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.models.merchant import Customer, CustomerSegment, Order, OrderStatus, Payment, PaymentStatus, Product, Refund, Subscription, SubscriptionStatus

SEED = 20260822
NOW = datetime(2026, 8, 22, tzinfo=UTC)


def uid(kind: str, number: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"revpilot/{SEED}/{kind}/{number}"))


def seed_database(reset: bool = False) -> dict[str, int]:
    rng = random.Random(SEED)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Customer)):
            if not reset:
                return {"customers": db.scalar(select(func.count()).select_from(Customer)), "seeded": 0}
            for table in (Refund, Payment, Order, Subscription, Product, Customer):
                db.execute(delete(table))
            db.commit()
        products = []
        catalog = [("Growth Starter", "Software", "799"), ("Revenue Pro", "Software", "1299"), ("Analytics Plus", "Analytics", "1899"), ("Priority Support", "Services", "499"), ("Checkout Kit", "Commerce", "999")]
        for i, (name, category, price) in enumerate(catalog):
            product = Product(id=uid("product", i), name=name, category=category, price=Decimal(price), views=0, orders_count=0, conversion_rate=Decimal("0"), created_at=NOW - timedelta(days=180))
            products.append(product)
            db.add(product)
        customers = []
        segments = [CustomerSegment.NEW] * 25 + [CustomerSegment.REGULAR] * 65 + [CustomerSegment.HIGH_VALUE] * 25 + [CustomerSegment.AT_RISK] * 30 + [CustomerSegment.INACTIVE] * 35
        for i, segment in enumerate(segments):
            customers.append(Customer(id=uid("customer", i), name=f"Merchant Customer {i + 1}", email=f"customer{i + 1}@demo.revpilot.local", segment=segment, total_spend=Decimal("0"), average_order_value=Decimal("0"), purchase_frequency=Decimal("0"), last_purchase_date=None, churn_probability=Decimal("0.75") if segment in (CustomerSegment.AT_RISK, CustomerSegment.INACTIVE) else Decimal("0.12"), created_at=NOW - timedelta(days=300 - i)))
        db.add_all(customers)
        db.flush()
        successful: dict[str, list[Decimal]] = {customer.id: [] for customer in customers}
        order_number = 0
        def create_order(customer: Customer, product: Product, status: OrderStatus, days_ago: int, failed: bool = False, retry: bool = False, attempt: int = 0):
            nonlocal order_number
            order_number += 1
            started = NOW - timedelta(days=days_ago, minutes=rng.randint(5, 900))
            order = Order(id=uid("order", order_number), customer_id=customer.id, product_id=product.id, amount=product.price, status=status, checkout_started_at=started, checkout_completed_at=started + timedelta(minutes=3) if status == OrderStatus.COMPLETED else None, created_at=started)
            db.add(order); product.orders_count += 1
            if status != OrderStatus.ABANDONED:
                payment = Payment(id=uid("payment", order_number), customer_id=customer.id, order_id=order.id, amount=order.amount, status=PaymentStatus.FAILED if failed else PaymentStatus.SUCCEEDED, payment_method="upi" if failed else rng.choice(["card", "upi", "netbanking"]), failure_reason="issuer_declined" if failed else None, retry_count=attempt, retry_eligible=retry, created_at=started + timedelta(minutes=2))
                db.add(payment)
                if not failed: successful[customer.id].append(order.amount)
            return order
        for i, customer in enumerate(customers):
            count = 4 if customer.segment == CustomerSegment.HIGH_VALUE else 2
            if customer.segment == CustomerSegment.INACTIVE: count = 2
            for j in range(count): create_order(customer, products[(i + j) % len(products)], OrderStatus.COMPLETED, 120 + j * 25 if customer.segment == CustomerSegment.INACTIVE else rng.randint(2, 100))
        retry_customers = customers[25:115]
        for i in range(320):
            customer = retry_customers[i % len(retry_customers)]
            create_order(customer, products[i % 3], OrderStatus.PENDING, rng.randint(0, 6), failed=True, retry=i < 270, attempt=i // len(retry_customers))
        for i in range(85): create_order(customers[115 + i % 35], products[3 if i < 60 else 4], OrderStatus.ABANDONED, rng.randint(1, 35))
        db.flush()
        for product in products:
            product.views = product.orders_count * (8 if product.name == "Checkout Kit" else rng.randint(3, 7))
            product.conversion_rate = Decimal(product.orders_count) / Decimal(product.views)
        for customer in customers:
            amounts = successful[customer.id]
            if amounts:
                customer.total_spend = sum(amounts, Decimal("0")); customer.average_order_value = customer.total_spend / len(amounts); customer.purchase_frequency = Decimal(len(amounts)) / Decimal("6"); customer.last_purchase_date = max(order.created_at for order in customer.orders if order.status == OrderStatus.COMPLETED)
        for i, customer in enumerate(customers[:90]):
            db.add(Subscription(id=uid("subscription", i), customer_id=customer.id, plan="Enterprise" if i < 12 else "Growth", amount=Decimal("2999") if i < 12 else Decimal("799"), status=SubscriptionStatus.PAST_DUE if 25 <= i < 42 else (SubscriptionStatus.CANCELLED if 42 <= i < 50 else SubscriptionStatus.ACTIVE), next_billing_date=NOW + timedelta(days=15), failed_attempts=2 if 25 <= i < 42 else 0, created_at=NOW - timedelta(days=100)))
        db.flush()
        paid = db.scalars(select(Payment).where(Payment.status == PaymentStatus.SUCCEEDED).limit(18)).all()
        for i, payment in enumerate(paid): db.add(Refund(id=uid("refund", i), payment_id=payment.id, amount=payment.amount if i < 3 else payment.amount / 2, reason="duplicate_charge" if i < 3 else "customer_request", created_at=payment.created_at + timedelta(days=2)))
        db.commit()
        return {"customers": len(customers), "products": len(products), "orders": order_number, "failed_payments": 320, "retry_eligible_payments": 270, "subscriptions": 90, "refunds": 18, "seeded": 1}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--reset", action="store_true")
    print(seed_database(parser.parse_args().reset))
