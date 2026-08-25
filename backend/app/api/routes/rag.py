"""Phase 8 - RAG API routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.rag.rag_engine import (
    ingest_knowledge_base,
    retrieve_similar_cases,
    retrieve_with_evidence_grounding,
)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 3
    category_filter: Optional[str] = None
    min_score: float = 0.05


class GroundedRetrieveRequest(BaseModel):
    query: str
    current_evidence: dict
    top_k: int = 3


@router.post("/ingest")
def ingest(_: dict = Depends(get_current_user)):
    return ingest_knowledge_base()


@router.post("/retrieve")
def retrieve(request: RetrieveRequest, _: dict = Depends(get_current_user)):
    results = retrieve_similar_cases(
        query=request.query,
        top_k=request.top_k,
        category_filter=request.category_filter,
        min_score=request.min_score,
    )
    return {"query": request.query, "results": results, "count": len(results)}


@router.post("/retrieve-grounded")
def retrieve_grounded(request: GroundedRetrieveRequest, _: dict = Depends(get_current_user)):
    results = retrieve_with_evidence_grounding(
        query=request.query,
        current_evidence=request.current_evidence,
        top_k=request.top_k,
    )
    return {"query": request.query, "results": results, "count": len(results)}
