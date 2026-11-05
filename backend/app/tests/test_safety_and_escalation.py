import pytest
from app.services.confidence_engine import safety_engine
from app.services.retrieval_validation import retrieval_validator
from app.schemas.emergency import ExtractedEmergencyInfo
from app.schemas.classification import ClassificationResult, PriorityLevel
from app.schemas.retrieval import RetrievedChunk, RelevanceStatus
from app.schemas.response import SystemOutcome

def test_critical_emergency_triggers_immediate_bypass():
    """Verify that life-threatening symptoms trigger Outcome E and bypass delays."""
    extracted = ExtractedEmergencyInfo(
        incident_type="cardiac_arrest",
        symptoms=["unconsciousness", "not breathing"],
        affected_body_parts=["chest"],
        severity_indicators=["Compromised airway or consciousness"],
        duration="3 minutes",
        age=55,
        location="unspecified",
        input_type="text",
        missing_information=[],
        is_life_threatening=True
    )
    classification = ClassificationResult(
        priority=PriorityLevel.CRITICAL,
        confidence=0.98,
        class_probabilities={"LOW": 0.0, "MODERATE": 0.01, "HIGH": 0.01, "CRITICAL": 0.98},
        decision_factors=["Critical keyword: cardiac arrest"],
        is_critical=True,
        requires_emergency_bypass=True
    )
    # Even with empty retrieval, critical bypass MUST trigger
    retrieval_val = retrieval_validator.validate_retrieval("cardiac arrest", [])
    
    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text="Patient collapsed, not breathing, cardiac arrest"
    )
    
    assert result["outcome"] == SystemOutcome.CRITICAL_EMERGENCY
    assert result["is_critical_bypass"] is True
    assert result["immediate_emergency_warning"] is not None

def test_low_retrieval_relevance_withholds_unsupported_guidance():
    """Verify industry review requirement: Low relevance chunks are rejected."""
    extracted = ExtractedEmergencyInfo(
        incident_type="unknown_emergency",
        symptoms=["strange purple rash on fingertip"],
        affected_body_parts=["finger"],
        severity_indicators=[],
        duration="2 days",
        age=30,
        location="unspecified",
        input_type="text",
        missing_information=[]
    )
    classification = ClassificationResult(
        priority=PriorityLevel.LOW,
        confidence=0.75,
        class_probabilities={"LOW": 0.75, "MODERATE": 0.20, "HIGH": 0.05, "CRITICAL": 0.0},
        decision_factors=["Minor symptom"],
        is_critical=False
    )
    # Low similarity chunk (below 0.52 threshold)
    low_sim_chunk = RetrievedChunk(
        chunk_id="kb-test-1",
        document_title="Cardiac Arrest Guide",
        source_name="AHA",
        section="Adult CPR",
        content="Perform chest compressions...",
        similarity_score=0.22,
        is_relevant=False
    )
    retrieval_val = retrieval_validator.validate_retrieval(
        query="strange purple rash on fingertip",
        retrieved_chunks=[low_sim_chunk]
    )
    assert retrieval_val.status == RelevanceStatus.IRRELEVANT
    assert retrieval_val.has_sufficient_evidence is False

    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text="I have a strange purple rash on my fingertip for 2 days"
    )
    assert result["outcome"] == SystemOutcome.LOW_RETRIEVAL_RELEVANCE
    assert "withheld" in result["immediate_emergency_warning"].lower()

def test_ambiguous_input_triggers_clarification():
    """Verify that ambiguous 1-2 word descriptions trigger clarification questions."""
    extracted = ExtractedEmergencyInfo(
        incident_type="unknown_emergency",
        symptoms=["unspecified acute distress"],
        affected_body_parts=["general/unspecified"],
        severity_indicators=[],
        duration="unknown",
        age=None,
        location="unspecified",
        input_type="text",
        missing_information=["What specific symptoms is the person experiencing?"]
    )
    classification = ClassificationResult(
        priority=PriorityLevel.MODERATE,
        confidence=0.50,
        class_probabilities={"LOW": 0.25, "MODERATE": 0.50, "HIGH": 0.20, "CRITICAL": 0.05},
        decision_factors=["Uncertain description"],
        is_critical=False
    )
    retrieval_val = retrieval_validator.validate_retrieval("help hurt", [])
    
    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text="help hurt"
    )
    assert result["outcome"] == SystemOutcome.AMBIGUOUS_INPUT
    assert len(result["clarification_questions"]) > 0
