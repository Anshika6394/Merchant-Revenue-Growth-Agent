"""Phase 10 - Actions API route."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.action_simulator import simulate_action, get_actions, submit_feedback

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])

class SimulateRequest(BaseModel):
    opportunity_id: Optional[str] = None
    action_type: str
    target_count: int
    avg_value: float = 5000.0

class FeedbackRequest(BaseModel):
    feedback: str
    status: str = "successful"

@router.post("/simulate")
def run_simulation(req: SimulateRequest, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return simulate_action(db, req.opportunity_id, req.action_type, req.target_count, req.avg_value)

@router.get("/")
def list_actions(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return get_actions(db)

@router.post("/{action_id}/feedback")
def action_feedback(action_id: str, req: FeedbackRequest, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return submit_feedback(db, action_id, req.feedback, req.status)
