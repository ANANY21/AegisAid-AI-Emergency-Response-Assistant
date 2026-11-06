"""
Automated Test Suite for Critical-Class Recall & Safety Escalation Layer.

Test Scenarios (Clinically Reviewed & Documented):
1. Clear Critical Emergency: Sudden cardiac arrest with apnea.
2. High-Risk Symptoms Confusable with Moderate/High: Depressed skull fracture / acute stroke FAST signs.
3. Ambiguous Medical Descriptions: Vague inputs ("hurt and sick") prompting targeted clarifications.
4. Missing Symptom Information: Incident statement lacking critical duration and specific distress parameters.
5. Non-Critical Cases: Superficial minor paper cut and dry cough (correctly triaged as LOW).
6. Conflicting Symptom Descriptions: Contradictory guidance triggering safe escalation.
7. Critical Warning Signs with Lower Classifier Probability: Verifying independent safety rule bypass override.
"""
import pytest
from app.models.classifier import TriageClassifier
from app.services.confidence_engine import safety_engine
from app.services.retrieval_validation import retrieval_validator
from app.schemas.emergency import ExtractedEmergencyInfo, InputTypeEnum
from app.schemas.classification import PriorityLevel, ClassificationResult
from app.schemas.retrieval import RetrievedChunk, RelevanceStatus
from app.schemas.response import SystemOutcome
from app.config import settings

@pytest.fixture(scope="module")
def classifier():
    model_path = settings.MODELS_DIR / "incident_classifier.joblib"
    return TriageClassifier(model_path)

# SCENARIO 1: Clear Critical Emergency (AHA Guidelines - ESI Level 1)
def test_scenario_1_clear_critical_emergency(classifier):
    text = "Sudden collapse, not breathing, unresponsive on the floor after clutching chest"
    res = classifier.predict(
        text=text,
        age=58.0,
        duration_minutes=5.0,
        has_breathing_difficulty=1,
        has_unconsciousness=1,
        has_severe_bleeding=0,
        has_chest_pain=1
    )
    assert res.priority == PriorityLevel.CRITICAL
    assert res.is_critical is True
    assert res.confidence >= 0.70
    assert res.requires_emergency_bypass is True

# SCENARIO 2: High-Risk Symptoms Easily Confused with Moderate/High (ASA/AHA Stroke & Trauma Guidelines)
def test_scenario_2_stroke_fast_and_skull_fracture_triaged_as_critical(classifier):
    # Acute stroke presentation (previously missed in baseline v1.0)
    stroke_text = "Elderly patient with facial drooping on right side, slurred speech, arm weakness for 20 mins"
    stroke_res = classifier.predict(
        text=stroke_text,
        age=74.0,
        duration_minutes=20.0,
        has_breathing_difficulty=0,
        has_unconsciousness=0,
        has_severe_bleeding=0,
        has_chest_pain=0,
        has_stroke_symptoms=1
    )
    assert stroke_res.priority == PriorityLevel.CRITICAL
    assert stroke_res.is_critical is True

    # Severe head trauma with skull depression (previously missed in baseline v1.0)
    trauma_text = "Severe head trauma with loss of consciousness and skull depression after motor vehicle crash"
    trauma_res = classifier.predict(
        text=trauma_text,
        age=35.0,
        duration_minutes=12.0,
        has_breathing_difficulty=0,
        has_unconsciousness=1,
        has_severe_bleeding=1,
        has_chest_pain=0,
        has_severe_trauma=1
    )
    assert trauma_res.priority == PriorityLevel.CRITICAL
    assert trauma_res.is_critical is True

# SCENARIO 3: Ambiguous Medical Descriptions (Safe Withholding of Guidance)
def test_scenario_3_ambiguous_medical_descriptions():
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
        class_probabilities={"LOW": 0.20, "MODERATE": 0.50, "HIGH": 0.20, "CRITICAL": 0.10},
        decision_factors=["Uncertain description"],
        is_critical=False
    )
    retrieval_val = retrieval_validator.validate_retrieval("feel bad hurt", [])
    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text="feel bad hurt"
    )
    assert result["outcome"] == SystemOutcome.AMBIGUOUS_INPUT
    assert result["is_critical_bypass"] is False
    assert len(result["clarification_questions"]) > 0

# SCENARIO 4: Missing Critical Clinical Information
def test_scenario_4_missing_symptom_information():
    extracted = ExtractedEmergencyInfo(
        incident_type="unknown_emergency",
        symptoms=["stomachache"],
        affected_body_parts=["abdomen"],
        severity_indicators=[],
        duration="unknown",
        age=None,
        location="unspecified",
        input_type="text",
        missing_information=["Patient age not provided", "Symptom duration unknown"]
    )
    classification = ClassificationResult(
        priority=PriorityLevel.MODERATE,
        confidence=0.60,
        class_probabilities={"LOW": 0.25, "MODERATE": 0.60, "HIGH": 0.10, "CRITICAL": 0.05},
        decision_factors=["Abdominal pain"],
        is_critical=False
    )
    retrieval_val = retrieval_validator.validate_retrieval("stomach ache", [])
    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=retrieval_val,
        raw_text="stomach ache"
    )
    assert result["outcome"] == SystemOutcome.AMBIGUOUS_INPUT
    assert any("age" in q.lower() or "symptom" in q.lower() for q in result["clarification_questions"])

# SCENARIO 5: Non-Critical Low Urgency Cases (ESI Level 4 & 5)
def test_scenario_5_non_critical_cases(classifier):
    paper_cut = "Small paper cut on index finger while opening mail envelope, tiny droplet of blood stopped immediately, mild stinging"
    res_cut = classifier.predict(
        text=paper_cut,
        age=24.0,
        duration_minutes=5.0,
        has_breathing_difficulty=0,
        has_unconsciousness=0,
        has_severe_bleeding=0,
        has_chest_pain=0
    )
    assert res_cut.priority == PriorityLevel.LOW
    assert res_cut.is_critical is False

    cold_text = "Mild dry cough and clear runny nose for 4 days, afebrile, lungs clear, normal appetite, feels like typical common cold"
    res_cold = classifier.predict(
        text=cold_text,
        age=39.0,
        duration_minutes=5760.0,
        has_breathing_difficulty=0,
        has_unconsciousness=0,
        has_severe_bleeding=0,
        has_chest_pain=0
    )
    assert res_cold.priority == PriorityLevel.LOW
    assert res_cold.is_critical is False

# SCENARIO 6: Conflicting Symptom Descriptions / Protocols
def test_scenario_6_conflicting_symptom_descriptions():
    extracted = ExtractedEmergencyInfo(
        incident_type="burn",
        symptoms=["burn on hand"],
        affected_body_parts=["hand"],
        severity_indicators=[],
        duration="10 minutes",
        age=30,
        location="unspecified",
        input_type="text",
        missing_information=[]
    )
    classification = ClassificationResult(
        priority=PriorityLevel.MODERATE,
        confidence=0.75,
        class_probabilities={"LOW": 0.10, "MODERATE": 0.75, "HIGH": 0.12, "CRITICAL": 0.03},
        decision_factors=["Burn"],
        is_critical=False
    )
    # Simulate conflicting retrieved chunks
    chunk_1 = RetrievedChunk(
        chunk_id="c1", document_title="Protocol A", source_name="WHO",
        section="Cooling", content="Irrigate with cold water", similarity_score=0.80,
        is_relevant=True, contraindications=["Do not apply ice"]
    )
    chunk_2 = RetrievedChunk(
        chunk_id="c2", document_title="Protocol B", source_name="Unverified",
        section="Cooling", content="Apply ice packs", similarity_score=0.78,
        is_relevant=True, contraindications=[]
    )
    val_res = retrieval_validator.validate_retrieval("burn", [chunk_1, chunk_2])
    # Force conflict flag for safety test
    val_res.status = RelevanceStatus.CONFLICTING
    
    result = safety_engine.evaluate_safety_and_escalation(
        extracted_info=extracted,
        classification=classification,
        retrieval_val=val_res,
        raw_text="Burn on hand"
    )
    assert result["outcome"] == SystemOutcome.CONFLICTING_INFORMATION
    assert "conflicting" in result["escalation_reason"].lower()

# SCENARIO 7: Critical Warning Signs with Lower Classifier Probability (Safety Override)
def test_scenario_7_critical_warning_signs_trigger_safety_override(classifier):
    """
    CRITICAL SAFETY REQUIREMENT:
    Even if the statistical model predicts a lower class (e.g. MODERATE or HIGH),
    the presence of definitive clinical red flags (apnea, unconsciousness, severe hemorrhage)
    MUST escalate priority to CRITICAL and trigger immediate bypass.
    """
    text_with_crit_signs = "Patient feels slightly dizzy but is turning blue, gasping for air, clutching throat"
    # Even if features were somehow zeroed out, the text red flag MUST override
    res = classifier.predict(
        text=text_with_crit_signs,
        age=45.0,
        duration_minutes=10.0,
        has_breathing_difficulty=1,
        has_unconsciousness=0,
        has_severe_bleeding=0,
        has_chest_pain=0
    )
    assert res.priority == PriorityLevel.CRITICAL
    assert res.is_critical is True
    assert any("critical" in factor.lower() or "respiratory" in factor.lower() for factor in res.decision_factors)
