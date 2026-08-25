from app.seed import seed_database


def auth_headers(client):
    client.post("/api/v1/auth/register", json={"email": "analytics@example.com", "password": "secure-password"})
    token = client.post("/api/v1/auth/login", data={"username": "analytics@example.com", "password": "secure-password"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_analytics_endpoints_require_authentication(client):
    assert client.get("/api/v1/analytics/overview").status_code == 401


def test_revenue_metrics_are_database_derived(client):
    seed_database(reset=True)
    response = client.get("/api/v1/analytics/revenue", headers=auth_headers(client))
    assert response.status_code == 200
    data = response.json()
    assert data["gross_revenue"] == "450590.00"
    assert float(data["net_revenue"]) == 438800.5
    assert float(data["successful_payment_revenue"]) == 450590
    assert data["order_count"] == 410
    assert data["transaction_count"] == 730
    assert float(data["aov"]) == 1099


def test_payments_include_configurable_recoverable_revenue(client):
    seed_database(reset=True)
    response = client.get("/api/v1/analytics/payments?recovery_assumption=0.40", headers=auth_headers(client))
    assert response.status_code == 200
    recoverable = response.json()["recoverable_revenue"]
    assert recoverable["eligible_payment_count"] == 270
    assert recoverable["eligible_customer_count"] == 90
    assert recoverable["failed_value"] == "359730.00"
    assert float(recoverable["recovery_assumption"]) == 0.4
    assert float(recoverable["estimated_recoverable_revenue"]) == 143892


def test_overview_checkout_customer_subscription_refund_and_trend_metrics(client):
    seed_database(reset=True)
    response = client.get("/api/v1/analytics/overview", headers=auth_headers(client))
    assert response.status_code == 200
    data = response.json()
    assert data["checkout"]["checkout_starts"] == 815
    assert data["checkout"]["abandoned_checkouts"] == 85
    assert data["checkout"]["abandoned_value"] == "54915.00"
    assert data["customers"]["repeat_customers"] == 180
    assert data["customers"]["win_back_signals"] == 65
    assert data["subscriptions"] == {"active": 65, "cancelled": 8, "past_due": 17, "failed_recurring_payments": 34, "subscription_revenue": "78335.00", "retention_risk": 17}
    assert data["refunds"]["refund_count"] == 18
    assert float(data["refunds"]["refund_value"]) == 11789.5
    assert "daily" in data["trends"]
    assert "previous_period_comparison" in data["trends"]
