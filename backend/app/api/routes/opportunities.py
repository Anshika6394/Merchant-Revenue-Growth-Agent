from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.opportunity_service import detect_opportunities, get_opportunities, get_opportunity

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])

@router.get("/")
def list_opportunities(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return get_opportunities(db)

@router.get("/{opportunity_id}")
def get_one(opportunity_id: str, db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return get_opportunity(db, opportunity_id)

@router.post("/detect")
def run_detect(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return detect_opportunities(db)
