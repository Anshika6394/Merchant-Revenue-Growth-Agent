"""Phase 8 - RAG Engine: ingestion, embedding, retrieval."""
from __future__ import annotations
import json
import math
from typing import Any

from app.rag.knowledge_base import BUSINESS_CASES

# ---------------------------------------------------------------------------
# Lightweight TF-IDF vector store (no external infrastructure needed)
# ---------------------------------------------------------------------------

class _TFIDFStore:
    """Minimal TF-IDF based vector store for local development."""

    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []
        self.vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}

    # ------------------------------------------------------------------
    def _tokenize(self, text: str) -> list[str]:
        return text.lower().replace(",", " ").replace(".", " ").split()

    def _tf(self, tokens: list[str]) -> dict[str, float]:
        freq: dict[str, float] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        total = len(tokens) or 1
        return {k: v / total for k, v in freq.items()}

    def _build_idf(self) -> None:
        N = len(self.docs)
        df: dict[str, int] = {}
        for vec in self.vectors:
            for term in vec:
                df[term] = df.get(term, 0) + 1
        self.idf = {t: math.log((N + 1) / (d + 1)) + 1 for t, d in df.items()}

    def _tfidf(self, tf: dict[str, float]) -> dict[str, float]:
        return {t: v * self.idf.get(t, 1.0) for t, v in tf.items()}

    def _cosine(self, a: dict[str, float], b: dict[str, float]) -> float:
        keys = set(a) & set(b)
        dot = sum(a[k] * b[k] for k in keys)
        mag_a = math.sqrt(sum(v * v for v in a.values())) or 1
        mag_b = math.sqrt(sum(v * v for v in b.values())) or 1
        return dot / (mag_a * mag_b)

    # ------------------------------------------------------------------
    def ingest(self, docs: list[dict[str, Any]]) -> None:
        """Ingest documents and build index."""
        self.docs = docs
        self.vectors = []
        for doc in docs:
            text = _doc_to_text(doc)
            tokens = self._tokenize(text)
            self.vectors.append(self._tf(tokens))
        self._build_idf()
        # Apply IDF weighting
        self.vectors = [self._tfidf(v) for v in self.vectors]

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        category_filter: str | None = None,
        min_score: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Retrieve top-k relevant documents for a query."""
        tokens = self._tokenize(query)
        tf = self._tf(tokens)
        q_vec = self._tfidf(tf)

        scores: list[tuple[float, int]] = []
        for i, doc_vec in enumerate(self.vectors):
            if category_filter and self.docs[i].get("category") != category_filter:
                continue
            score = self._cosine(q_vec, doc_vec)
            if score >= min_score:
                scores.append((score, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, idx in scores[:top_k]:
            doc = self.docs[idx]
            results.append({
                "case_id": doc["id"],
                "category": doc["category"],
                "similarity_score": round(score, 4),
                "relevance": _score_to_relevance(score),
                "case": doc,
                "why_applicable": _explain_match(query, doc),
            })
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_to_text(doc: dict[str, Any]) -> str:
    parts = [
        doc.get("problem", ""),
        doc.get("context", ""),
        doc.get("action", ""),
        doc.get("result", ""),
        " ".join(doc.get("tags", [])),
        " ".join(doc.get("applicable_conditions", [])),
        doc.get("category", ""),
    ]
    return " ".join(parts)


def _score_to_relevance(score: float) -> str:
    if score >= 0.4:
        return "high"
    if score >= 0.15:
        return "medium"
    return "low"


def _explain_match(query: str, doc: dict[str, Any]) -> str:
    q_lower = query.lower()
    tags = doc.get("tags", [])
    matched = [t for t in tags if t in q_lower]
    if matched:
        return f"Query matches case tags: {', '.join(matched)}. Case addresses: {doc['problem']}"
    return f"Semantic similarity to case: {doc['problem']}"


# ---------------------------------------------------------------------------
# Singleton store
# ---------------------------------------------------------------------------

_store: _TFIDFStore | None = None


def get_store() -> _TFIDFStore:
    global _store
    if _store is None:
        _store = _TFIDFStore()
        _store.ingest(BUSINESS_CASES)
    return _store


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_knowledge_base() -> dict[str, Any]:
    """Ingest all business cases and return stats."""
    store = _TFIDFStore()
    store.ingest(BUSINESS_CASES)
    global _store
    _store = store
    return {
        "status": "ok",
        "documents_ingested": len(BUSINESS_CASES),
        "categories": list({c["category"] for c in BUSINESS_CASES}),
    }


def retrieve_similar_cases(
    query: str,
    top_k: int = 3,
    category_filter: str | None = None,
    min_score: float = 0.05,
) -> list[dict[str, Any]]:
    """Retrieve semantically similar historical cases."""
    return get_store().retrieve(query, top_k=top_k, category_filter=category_filter, min_score=min_score)


def retrieve_with_evidence_grounding(
    query: str,
    current_evidence: dict[str, Any],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve cases and compare against current merchant evidence."""
    raw = retrieve_similar_cases(query, top_k=top_k)
    grounded = []
    for r in raw:
        case = r["case"]
        comparison = _compare_evidence(current_evidence, case.get("evidence", {}))
        r["evidence_comparison"] = comparison
        r["grounding_note"] = _grounding_note(comparison)
        grounded.append(r)
    return grounded


def _compare_evidence(current: dict[str, Any], historical: dict[str, Any]) -> dict[str, Any]:
    shared_keys = set(current.keys()) & set(historical.keys())
    comparison = {}
    for k in shared_keys:
        try:
            c_val = float(current[k])
            h_val = float(historical[k])
            comparison[k] = {"current": c_val, "historical": h_val, "ratio": round(c_val / h_val, 2) if h_val else None}
        except (TypeError, ValueError):
            pass
    return comparison


def _grounding_note(comparison: dict[str, Any]) -> str:
    if not comparison:
        return "No direct evidence overlap; case applies by category similarity."
    notes = []
    for k, v in comparison.items():
        ratio = v.get("ratio")
        if ratio is not None:
            if 0.5 <= ratio <= 2.0:
                notes.append(f"{k} is comparable (current: {v['current']}, historical: {v['historical']})")
            elif ratio > 2.0:
                notes.append(f"{k} is higher than historical case ({v['current']} vs {v['historical']})")
            else:
                notes.append(f"{k} is lower than historical case ({v['current']} vs {v['historical']})")
    return "; ".join(notes) if notes else "Evidence partially comparable."
