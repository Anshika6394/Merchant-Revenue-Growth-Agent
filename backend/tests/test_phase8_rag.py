"""Phase 8 - RAG tests."""
import pytest
from app.rag.rag_engine import (
    ingest_knowledge_base,
    retrieve_similar_cases,
    retrieve_with_evidence_grounding,
    get_store,
)


def test_ingest_returns_correct_count():
    result = ingest_knowledge_base()
    assert result["status"] == "ok"
    assert result["documents_ingested"] == 8


def test_ingest_returns_categories():
    result = ingest_knowledge_base()
    assert "payment_recovery" in result["categories"]
    assert "checkout_recovery" in result["categories"]


def test_retrieve_payment_query():
    results = retrieve_similar_cases("payment failure retry recovery")
    assert len(results) > 0
    assert any(r["category"] == "payment_recovery" for r in results)


def test_retrieve_checkout_query():
    results = retrieve_similar_cases("checkout abandonment cart recovery")
    assert len(results) > 0
    assert any(r["category"] == "checkout_recovery" for r in results)


def test_retrieve_subscription_query():
    results = retrieve_similar_cases("subscription churn retention past due")
    assert len(results) > 0
    assert any(r["category"] == "subscription_retention" for r in results)


def test_retrieve_winback_query():
    results = retrieve_similar_cases("inactive customer winback campaign")
    assert len(results) > 0


def test_retrieve_refund_query():
    results = retrieve_similar_cases("refund leakage product quality")
    assert len(results) > 0
    assert any(r["category"] == "refund_leakage" for r in results)


def test_metadata_filtering_by_category():
    results = retrieve_similar_cases(
        "revenue recovery",
        category_filter="payment_recovery"
    )
    for r in results:
        assert r["category"] == "payment_recovery"


def test_irrelevant_query_low_or_no_results():
    results = retrieve_similar_cases("banana mango fruit salad", min_score=0.3)
    assert len(results) == 0


def test_retrieve_results_have_required_keys():
    results = retrieve_similar_cases("payment failure", top_k=1)
    if results:
        r = results[0]
        assert "case_id" in r
        assert "category" in r
        assert "similarity_score" in r
        assert "relevance" in r
        assert "case" in r
        assert "why_applicable" in r


def test_similarity_score_between_0_and_1():
    results = retrieve_similar_cases("payment recovery retry")
    for r in results:
        assert 0.0 <= r["similarity_score"] <= 1.0


def test_top_k_respected():
    results = retrieve_similar_cases("payment checkout recovery", top_k=2)
    assert len(results) <= 2


def test_grounded_retrieval_has_evidence_comparison():
    evidence = {"failed_payments": 100, "failure_rate": 0.3, "failed_value": 200000}
    results = retrieve_with_evidence_grounding(
        query="payment failure recovery",
        current_evidence=evidence,
        top_k=2,
    )
    assert len(results) > 0
    for r in results:
        assert "evidence_comparison" in r
        assert "grounding_note" in r


def test_grounding_note_not_empty():
    evidence = {"failed_payments": 50, "failure_rate": 0.25}
    results = retrieve_with_evidence_grounding(
        query="payment retry campaign",
        current_evidence=evidence,
    )
    for r in results:
        assert isinstance(r["grounding_note"], str)
        assert len(r["grounding_note"]) > 0


def test_store_is_singleton():
    s1 = get_store()
    s2 = get_store()
    assert s1 is s2


def test_retrieve_product_growth_query():
    results = retrieve_similar_cases("product low conversion growth visibility")
    assert len(results) > 0
    assert any(r["category"] == "product_growth" for r in results)
