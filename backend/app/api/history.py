from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database.connection import get_db
from ..database.repositories import EmergencyRepository

router = APIRouter(prefix="/api/history", tags=["Emergency History"])

@router.get("", response_model=List[Dict[str, Any]])
def get_session_history(limit: int = 30, db: Session = Depends(get_db)):
    records = EmergencyRepository.get_recent_sessions(db, limit=limit)
    results = []
    for r in records:
        inp = r.inputs[0] if r.inputs else None
        cls = r.classification
        resp = r.response
        results.append({
            "session_id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "priority": r.priority,
            "outcome": r.outcome,
            "is_critical_bypass": r.is_critical_bypass,
            "raw_description": inp.raw_description if inp else "N/A",
            "summary": resp.summary if resp else "N/A",
            "extracted_symptoms": inp.extracted_data.get("symptoms", []) if inp and inp.extracted_data else []
        })
    return results

@router.delete("/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    success = EmergencyRepository.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session record not found")
    return {"status": "success", "message": f"Session {session_id} deleted"}

@router.delete("")
def clear_all_history(db: Session = Depends(get_db)):
    count = EmergencyRepository.clear_all_history(db)
    return {"status": "success", "message": f"Cleared {count} historical session records"}
