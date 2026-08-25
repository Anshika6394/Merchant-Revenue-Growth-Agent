"""Synthetic business cases knowledge base for RAG."""

BUSINESS_CASES = [
    {
        "id": "case_001",
        "category": "payment_recovery",
        "problem": "High payment failure rate due to card declines",
        "context": "Merchant had 35% payment failure rate over 30 days with 120 failed transactions",
        "evidence": {"failed_payments": 120, "failure_rate": 0.35, "affected_customers": 80, "failed_value": 240000},
        "action": "Triggered automated retry campaign targeting customers with previous successful payments",
        "result": "Recovered 28% of failed payments within 7 days, INR 67200 recovered",
        "applicable_conditions": ["failure_rate > 0.2", "retry_eligible_customers > 20", "previous_success_rate > 0.7"],
        "tags": ["payment", "retry", "recovery", "card_decline"]
    },
    {
        "id": "case_002",
        "category": "checkout_recovery",
        "problem": "High checkout abandonment at payment step",
        "context": "62% abandonment rate with INR 180000 in abandoned cart value",
        "evidence": {"abandonment_rate": 0.62, "abandoned_value": 180000, "abandoned_count": 95},
        "action": "Sent targeted recovery emails within 1 hour of abandonment with simplified payment options",
        "result": "Recovered 22% of abandoned checkouts, INR 39600 recovered",
        "applicable_conditions": ["abandonment_rate > 0.4", "abandoned_value > 50000"],
        "tags": ["checkout", "abandonment", "recovery", "email"]
    },
    {
        "id": "case_003",
        "category": "customer_winback",
        "problem": "Valuable customers inactive for 90+ days",
        "context": "45 high-value customers with average spend INR 8000 had not purchased in 3 months",
        "evidence": {"inactive_customers": 45, "avg_previous_spend": 8000, "days_inactive": 90},
        "action": "Personalized win-back campaign with exclusive offer based on previous purchase history",
        "result": "18% reactivation rate, 8 customers returned, INR 64000 recovered",
        "applicable_conditions": ["inactive_days > 60", "previous_spend > 2000", "inactive_customers > 10"],
        "tags": ["winback", "retention", "inactive", "campaign"]
    },
    {
        "id": "case_004",
        "category": "subscription_retention",
        "problem": "Subscription payment failures causing involuntary churn",
        "context": "22 subscriptions in past-due state representing INR 55000 monthly recurring revenue at risk",
        "evidence": {"past_due_subscriptions": 22, "mrr_at_risk": 55000, "avg_subscription_value": 2500},
        "action": "Dunning campaign with payment method update request and grace period extension",
        "result": "Retained 65% of at-risk subscriptions, INR 35750 MRR preserved",
        "applicable_conditions": ["past_due_count > 5", "mrr_at_risk > 10000"],
        "tags": ["subscription", "dunning", "retention", "churn"]
    },
    {
        "id": "case_005",
        "category": "refund_leakage",
        "problem": "Concentrated refunds on specific product indicating quality issue",
        "context": "One product had 28% refund rate vs 4% baseline, INR 42000 in refunds over 60 days",
        "evidence": {"product_refund_rate": 0.28, "baseline_refund_rate": 0.04, "refund_value": 42000},
        "action": "Investigated product quality, updated description, improved packaging",
        "result": "Refund rate dropped to 6% within 30 days, saving INR 30000 monthly",
        "applicable_conditions": ["product_refund_rate > 2x_baseline", "refund_value > 10000"],
        "tags": ["refund", "quality", "leakage", "product"]
    },
    {
        "id": "case_006",
        "category": "product_growth",
        "problem": "High-converting product with low visibility",
        "context": "Product had 34% conversion rate but only 80 monthly views vs 400 for similar products",
        "evidence": {"conversion_rate": 0.34, "monthly_views": 80, "category_avg_views": 400},
        "action": "Increased product promotion budget, featured in homepage, improved SEO tags",
        "result": "Views increased to 310/month, revenue grew by INR 78000/month",
        "applicable_conditions": ["conversion_rate > 1.5x_baseline", "views < category_average"],
        "tags": ["product", "conversion", "growth", "visibility"]
    },
    {
        "id": "case_007",
        "category": "payment_recovery",
        "problem": "UPI payment failures during peak hours",
        "context": "UPI failure rate 41% between 8-10 PM, 200+ failed transactions",
        "evidence": {"upi_failure_rate": 0.41, "failed_transactions": 200, "peak_hour_losses": 89000},
        "action": "Added fallback payment methods, retried UPI failures after 15 min delay",
        "result": "Recovered 45% of peak-hour UPI failures, INR 40050 recovered",
        "applicable_conditions": ["payment_method == upi", "time_based_failure_pattern", "failure_rate > 0.3"],
        "tags": ["payment", "upi", "recovery", "peak_hours"]
    },
    {
        "id": "case_008",
        "category": "checkout_recovery",
        "problem": "Mobile checkout abandonment significantly higher than desktop",
        "context": "Mobile abandonment 71% vs desktop 38%, INR 95000 mobile cart value abandoned",
        "evidence": {"mobile_abandonment": 0.71, "desktop_abandonment": 0.38, "mobile_abandoned_value": 95000},
        "action": "Simplified mobile checkout to 2 steps, added UPI as primary option on mobile",
        "result": "Mobile abandonment dropped to 48%, INR 22000 additional monthly revenue",
        "applicable_conditions": ["mobile_abandonment > desktop_abandonment * 1.5"],
        "tags": ["checkout", "mobile", "ux", "abandonment"]
    }
]
