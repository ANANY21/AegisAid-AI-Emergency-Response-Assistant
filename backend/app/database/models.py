from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base
import uuid

class EmergencySessionRecord(Base):
    __tablename__ = "emergency_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="COMPLETED")
    priority = Column(String(20), nullable=False)
    outcome = Column(String(50), nullable=False)
    is_critical_bypass = Column(Boolean, default=False)
    
    # Store relationships
    inputs = relationship("EmergencyInputRecord", back_populates="session", cascade="all, delete-orphan")
    classification = relationship("ClassificationRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")
    retrieval = relationship("RetrievalRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")
    response = relationship("ResponseRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")
    escalation = relationship("EscalationEventRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")

class EmergencyInputRecord(Base):
    __tablename__ = "emergency_inputs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("emergency_sessions.id"))
    input_type = Column(String(20), default="text")
    raw_description = Column(Text, nullable=False)
    voice_transcription = Column(Text, nullable=True)
    location_text = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    patient_age = Column(Integer, nullable=True)
    duration = Column(String(100), nullable=True)
    extracted_data = Column(JSON, nullable=True)
    
    session = relationship("EmergencySessionRecord", back_populates="inputs")

class ClassificationRecord(Base):
    __tablename__ = "classification_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("emergency_sessions.id"))
    priority = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    class_probabilities = Column(JSON, nullable=False)
    decision_factors = Column(JSON, nullable=True)
    model_version = Column(String(100), default="incident-rf-calibrated-v1")

    session = relationship("EmergencySessionRecord", back_populates="classification")

class RetrievalRecord(Base):
    __tablename__ = "retrieval_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("emergency_sessions.id"))
    status = Column(String(30), nullable=False)
    max_similarity = Column(Float, default=0.0)
    mean_similarity = Column(Float, default=0.0)
    has_sufficient_evidence = Column(Boolean, default=False)
    retrieved_chunks_json = Column(JSON, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    session = relationship("EmergencySessionRecord", back_populates="retrieval")

class ResponseRecord(Base):
    __tablename__ = "response_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("emergency_sessions.id"))
    summary = Column(Text, nullable=False)
    first_aid_steps_json = Column(JSON, nullable=True)
    precautions_json = Column(JSON, nullable=True)
    what_to_avoid_json = Column(JSON, nullable=True)
    sources_json = Column(JSON, nullable=True)
    llm_provider = Column(String(100), default="groq")
    faithfulness_score = Column(Float, default=1.0)

    session = relationship("EmergencySessionRecord", back_populates="response")

class EscalationEventRecord(Base):
    __tablename__ = "escalation_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("emergency_sessions.id"))
    trigger_type = Column(String(50), nullable=False) # CRITICAL_BYPASS, LOW_RELEVANCE, AMBIGUOUS_INPUT, CONFLICTING_INFO
    escalation_reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("EmergencySessionRecord", back_populates="escalation")
