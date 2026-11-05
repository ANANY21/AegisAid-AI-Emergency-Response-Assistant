from sqlalchemy.orm import Session
from .models import (
    EmergencySessionRecord, EmergencyInputRecord, ClassificationRecord,
    RetrievalRecord, ResponseRecord, EscalationEventRecord, Base
)
from .connection import engine
from typing import List, Optional, Dict, Any
from datetime import datetime

# Auto-create tables on import
Base.metadata.create_all(bind=engine)

class EmergencyRepository:
    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        priority: str,
        outcome: str,
        is_critical_bypass: bool = False
    ) -> EmergencySessionRecord:
        record = EmergencySessionRecord(
            id=session_id,
            priority=priority,
            outcome=outcome,
            is_critical_bypass=is_critical_bypass,
            created_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def save_full_session_log(
        db: Session,
        session_id: str,
        input_data: Dict[str, Any],
        extracted_data: Dict[str, Any],
        classification_data: Dict[str, Any],
        retrieval_data: Dict[str, Any],
        response_data: Dict[str, Any],
        escalation_data: Optional[Dict[str, Any]] = None
    ) -> EmergencySessionRecord:
        # Check or create session
        session = db.query(EmergencySessionRecord).filter(EmergencySessionRecord.id == session_id).first()
        if not session:
            session = EmergencySessionRecord(
                id=session_id,
                priority=classification_data.get("priority", "MODERATE"),
                outcome=response_data.get("outcome", "SUFFICIENT_EVIDENCE"),
                is_critical_bypass=classification_data.get("is_critical", False),
                created_at=datetime.utcnow()
            )
            db.add(session)
            db.flush()

        # Save Input Record
        inp_record = EmergencyInputRecord(
            session_id=session_id,
            input_type=input_data.get("input_type", "text"),
            raw_description=input_data.get("description", ""),
            voice_transcription=input_data.get("voice_transcription"),
            location_text=input_data.get("location_text"),
            latitude=input_data.get("latitude"),
            longitude=input_data.get("longitude"),
            patient_age=input_data.get("patient_age"),
            duration=input_data.get("duration"),
            extracted_data=extracted_data
        )
        db.add(inp_record)

        # Save Classification Record
        cls_record = ClassificationRecord(
            session_id=session_id,
            priority=classification_data.get("priority", "MODERATE"),
            confidence=classification_data.get("confidence", 0.0),
            class_probabilities=classification_data.get("class_probabilities", {}),
            decision_factors=classification_data.get("decision_factors", []),
            model_version=classification_data.get("model_version", "incident-rf-calibrated-v1")
        )
        db.add(cls_record)

        # Save Retrieval Record
        ret_record = RetrievalRecord(
            session_id=session_id,
            status=retrieval_data.get("status", "VALID"),
            max_similarity=retrieval_data.get("max_similarity", 0.0),
            mean_similarity=retrieval_data.get("mean_similarity", 0.0),
            has_sufficient_evidence=retrieval_data.get("has_sufficient_evidence", True),
            retrieved_chunks_json=retrieval_data.get("top_chunks", []),
            rejection_reason=retrieval_data.get("rejection_reason")
        )
        db.add(ret_record)

        # Save Response Record
        resp_record = ResponseRecord(
            session_id=session_id,
            summary=response_data.get("summary", ""),
            first_aid_steps_json=response_data.get("first_aid_steps", []),
            precautions_json=response_data.get("precautions", []),
            what_to_avoid_json=response_data.get("what_to_avoid", []),
            sources_json=response_data.get("sources", []),
            llm_provider=response_data.get("llm_provider", "Groq"),
            faithfulness_score=response_data.get("confidence_breakdown", {}).get("faithfulness_score", 1.0)
        )
        db.add(resp_record)

        # Save Escalation if triggered
        if escalation_data:
            esc_record = EscalationEventRecord(
                session_id=session_id,
                trigger_type=escalation_data.get("trigger_type", "UNKNOWN"),
                escalation_reason=escalation_data.get("reason", "")
            )
            db.add(esc_record)

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_recent_sessions(db: Session, limit: int = 50) -> List[EmergencySessionRecord]:
        return db.query(EmergencySessionRecord).order_by(EmergencySessionRecord.created_at.desc()).limit(limit).all()

    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        session = db.query(EmergencySessionRecord).filter(EmergencySessionRecord.id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    @staticmethod
    def clear_all_history(db: Session) -> int:
        count = db.query(EmergencySessionRecord).delete()
        db.commit()
        return count
