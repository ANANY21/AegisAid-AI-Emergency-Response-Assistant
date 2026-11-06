import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..database.repositories import EmergencyRepository
from ..schemas.emergency import EmergencyInputRequest
from ..schemas.response import EmergencyResponse
from ..services.preprocessing import clean_and_normalize_text
from ..services.speech_service import process_voice_transcription, transcribe_and_translate_audio_file
from ..services.image_service import analyze_emergency_image
from ..services.extraction_service import extract_emergency_information
from ..models.classifier import TriageClassifier
from ..services.rag_service import rag_service
from ..services.retrieval_validation import retrieval_validator
from ..services.confidence_engine import safety_engine
from ..services.generation_service import generation_service
from ..services.shap_service import shap_service
from ..config import settings
from ..core.logging import logger

router = APIRouter(prefix="/api/emergency", tags=["Emergency Response"])

# Initialize triage classifier instance
classifier = TriageClassifier(settings.MODELS_DIR / "incident_classifier.joblib")

class SpeechTranslationRequest(BaseModel):
    text: str

@router.post("/transcribe-audio")
async def transcribe_audio_endpoint(
    audio_file: UploadFile = File(...),
    translate: bool = Form(True)
):
    """
    Transcribes and translates emergency voice audio using Whisper API.
    Converts multi-language audio into structured English emergency descriptions.
    """
    file_bytes = await audio_file.read()
    result = transcribe_and_translate_audio_file(
        file_bytes=file_bytes,
        filename=audio_file.filename or "recording.webm",
        translate_to_english=translate
    )
    return result

@router.post("/translate-speech")
def translate_speech_endpoint(req: SpeechTranslationRequest):
    """
    Cleans, corrects medical terminology, and translates dictated foreign speech into English.
    """
    res = process_voice_transcription(req.text)
    return res

@router.post("/analyze", response_model=EmergencyResponse)
def analyze_emergency(
    payload: EmergencyInputRequest,
    db: Session = Depends(get_db)
):
    """
    Main deterministic backend orchestration pipeline:
    STAGE 1: Multimodal User Input & Preprocessing
    STAGE 2: Emergency Information Extraction (Pydantic structured schema)
    STAGE 3: Transformer-based Contextual Understanding
    STAGE 4: ML-based Calibrated Incident Prioritization (LOW, MODERATE, HIGH, CRITICAL)
    STAGE 5: Medical Knowledge Base Retrieval (RAG with source provenance)
    STAGE 6: Retrieval Relevance Validation (Relevance thresholding & conflict detection)
    STAGE 7: Confidence & Safety Escalation Engine (Outcomes A through E)
    STAGE 8: Grounded Generative Response Engine (Groq API or validated deterministic protocol)
    STAGE 9: Structured Session Persistence
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Initiating emergency analysis session: {session_id} | Modality: {payload.input_type}")

    # Stage 1: Input Preprocessing
    raw_desc = payload.description
    if payload.voice_transcription:
        voice_res = process_voice_transcription(payload.voice_transcription)
        raw_desc = f"{raw_desc} {voice_res['processed_text']}".strip()

    prep = clean_and_normalize_text(raw_desc)
    cleaned_text = prep["cleaned_text"]

    # Image processing if supplied
    image_analysis = {}
    if payload.image_base64:
        image_analysis = analyze_emergency_image(payload.image_base64, cleaned_text)
        if image_analysis.get("visible_observations"):
            cleaned_text += " [Image Findings: " + "; ".join(image_analysis["visible_observations"]) + "]"

    # Stage 2: Information Extraction
    extracted_info = extract_emergency_information(
        text=cleaned_text,
        input_type=payload.input_type.value,
        patient_age=payload.patient_age,
        duration=payload.duration,
        location_text=payload.location_text
    )

    # Stage 3 & 4: ML Classification
    has_unconscious = int("unconsciousness" in extracted_info.symptoms)
    has_breathing = int("difficulty breathing" in extracted_info.symptoms or "choking" in extracted_info.symptoms)
    has_bleeding = int("severe bleeding" in extracted_info.symptoms)
    has_chest = int("chest pain" in extracted_info.symptoms)
    has_stroke = int("facial droop" in extracted_info.symptoms or "slurred speech" in extracted_info.symptoms)
    has_anaphylaxis = int(any(w in cleaned_text.lower() for w in ["anaphylac", "stridor", "swollen tongue", "throat closing"]))
    has_trauma = int(any(w in cleaned_text.lower() for w in ["skull depression", "stab", "gunshot", "sucking chest", "motor vehicle crash", "amputation"]))
    has_ams = int(has_unconscious or any(w in cleaned_text.lower() for w in ["delirium", "heatstroke", "pinpoint pupils", "disoriented", "unresponsive"]))

    classification = classifier.predict(
        text=cleaned_text,
        age=float(extracted_info.age if extracted_info.age is not None else 35.0),
        duration_minutes=30.0,
        has_breathing_difficulty=has_breathing,
        has_unconsciousness=has_unconscious,
        has_severe_bleeding=has_bleeding,
        has_chest_pain=has_chest,
        has_stroke_symptoms=has_stroke,
        has_anaphylaxis_symptoms=has_anaphylaxis,
        has_severe_trauma=has_trauma,
        has_altered_mental_status=has_ams
    )

    # Stage 4b: Explainable AI Attribution (SHAP TreeExplainer)
    shap_summary = None
    try:
        shap_summary = shap_service.explain_prediction(
            text=cleaned_text,
            age=float(extracted_info.age if extracted_info.age is not None else 35.0),
            duration_minutes=30.0,
            has_breathing_difficulty=has_breathing,
            has_unconsciousness=has_unconscious,
            has_severe_bleeding=has_bleeding,
            has_chest_pain=has_chest,
            has_stroke_symptoms=has_stroke,
            has_anaphylaxis_symptoms=has_anaphylaxis,
            has_severe_trauma=has_trauma,
            has_altered_mental_status=has_ams
        )
    except Exception as e:
        logger.warning(f"SHAP explanation generation skipped for session {session_id}: {e}")

    # Stage 5: RAG Retrieval
    query_for_rag = f"{extracted_info.incident_type} {cleaned_text}"
    retrieved_chunks = rag_service.retrieve(query_for_rag, top_k=settings.RETRIEVAL_TOP_K)

    # Stage 6: Retrieval Relevance Validation (Critical Industry Review Requirement)
    retrieval_val = retrieval_validator.validate_retrieval(
        query=query_for_rag,
        retrieved_chunks=retrieved_chunks
    )

    # Stage 7: Confidence & Safety Escalation Engine
    safety_evaluation = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted_info,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text=cleaned_text
    )

    # Stage 8: Grounded Response Generation
    response = generation_service.generate_response(
        session_id=session_id,
        raw_description=cleaned_text,
        extracted_info=extracted_info,
        classification=classification,
        retrieval_val=retrieval_val,
        safety_evaluation=safety_evaluation,
        shap_summary=shap_summary
    )

    # Stage 9: Session Persistence
    try:
        EmergencyRepository.save_full_session_log(
            db=db,
            session_id=session_id,
            input_data={
                "description": payload.description,
                "input_type": payload.input_type.value,
                "voice_transcription": payload.voice_transcription,
                "location_text": payload.location_text,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "patient_age": payload.patient_age,
                "duration": payload.duration
            },
            extracted_data=extracted_info.model_dump(),
            classification_data=classification.model_dump(),
            retrieval_data=retrieval_val.model_dump(),
            response_data=response.model_dump(),
            escalation_data={
                "trigger_type": safety_evaluation["outcome"].value,
                "reason": safety_evaluation.get("escalation_reason", "")
            } if safety_evaluation["outcome"].value != "SUFFICIENT_EVIDENCE" else None
        )
    except Exception as e:
        logger.error(f"Failed to persist emergency session {session_id}: {e}")

    return response
