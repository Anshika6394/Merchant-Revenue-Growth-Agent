"""Phase 7 - Strategy Orchestrator API route."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.agents.strategy_orchestrator import StrategyOrchestrator
from app.tools.registry import registry

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

class StrategyRequest(BaseModel):
    query: str

@router.post("/strategy")
def run_strategy(
    request: StrategyRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    orchestrator = StrategyOrchestrator(registry)
    return orchestrator.run(query=request.query, db=db)
