from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.merchant import Customer, CustomerSegment, Order, OrderStatus, Payment, PaymentStatus, Product, Refund
from app.seed import seed_database


def test_order_payment_refund_relationships():
    with SessionLocal() as db:
        customer = Customer(id="customer-1", name="Test Customer", email="test@merchant.local", segment=CustomerSegment.REGULAR, total_spend=Decimal("999"), average_order_value=Decimal("999"), purchase_frequency=Decimal("1"), churn_probability=Decimal("0.1"), created_at=datetime.now(UTC))
        product = Product(id="product-1", name="Test Product", category="Test", price=Decimal("999"), views=10, orders_count=1, conversion_rate=Decimal("0.1"), created_at=datetime.now(UTC))
        order = Order(id="order-1", customer=customer, product=product, amount=Decimal("999"), status=OrderStatus.COMPLETED, checkout_started_at=datetime.now(UTC), checkout_completed_at=datetime.now(UTC), created_at=datetime.now(UTC))
        payment = Payment(id="payment-1", customer=customer, order=order, amount=order.amount, status=PaymentStatus.SUCCEEDED, payment_method="card", retry_count=0, retry_eligible=False, created_at=datetime.now(UTC))
        db.add(Refund(id="refund-1", payment=payment, amount=Decimal("99"), reason="customer_request", created_at=datetime.now(UTC)))
        db.commit()
        stored = db.scalar(select(Payment).where(Payment.id == "payment-1"))
        assert stored.order.customer.email == "test@merchant.local"
        assert stored.refunds[0].payment_id == stored.id


def test_seed_is_deterministic_and_idempotent():
    first = seed_database(reset=True)
    second = seed_database()
    with SessionLocal() as db:
        assert first["failed_payments"] == 320
        assert first["retry_eligible_payments"] == 270
        assert second["seeded"] == 0
        assert db.scalar(select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.FAILED)) == 320
