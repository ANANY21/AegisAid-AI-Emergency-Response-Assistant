import pytest
from pathlib import Path

from app.services.shap_service import shap_service
from app.services.source_registry import source_registry
from app.services.citation_service import citation_service
from app.schemas.sources import SourceReviewStatus, SourceReviewUpdateRequest
from app.schemas.retrieval import RetrievedChunk
from app.api.explainability import (
    explain_incident_prediction, get_global_model_explanations,
    ExplainabilityRequest
)
from app.api.sources import (
    list_medical_sources, get_source_registry_metrics,
    get_medical_source_by_id
)
from app.api.emergency import analyze_emergency
from app.schemas.emergency import EmergencyInputRequest, InputTypeEnum
from app.database.connection import SessionLocal

# ---------------------------------------------------------------------------
# TEST SUITE 1: Explainable AI using SHAP
# ---------------------------------------------------------------------------

def test_shap_service_initialization():
    """Verify that SHAP TreeExplainers are properly loaded across the calibrated ensemble."""
    assert shap_service is not None
    assert len(shap_service.explainers) >= 1
    assert len(shap_service.feature_names) == 1510
    assert "CRITICAL" in shap_service.classes

def test_shap_local_prediction_critical():
    """Verify SHAP local explanation for a critical cardiac emergency."""
    exp = shap_service.explain_prediction(
        text="Crushing chest pain radiating down left arm, cold sweat, difficulty breathing",
        age=58.0,
        has_breathing_difficulty=1,
        has_chest_pain=1,
        has_unconsciousness=0
    )
    assert exp["status"] == "success"
    assert exp["predicted_class"] == "CRITICAL"
    assert exp["base_value"] is not None
    assert exp["model_output_value"] is not None
    assert len(exp["feature_contributions"]) > 0
    assert isinstance(exp["class_probabilities"], dict)
    assert "CRITICAL" in exp["class_probabilities"]
    assert exp["class_probabilities"]["CRITICAL"] >= 0.20

def test_shap_multiclass_and_counterfactual():
    """Verify that user/reviewer can inspect SHAP values for alternate classes."""
    for cls_name in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
        exp = shap_service.explain_prediction(
            text="Mild ankle sprain while jogging, slight swelling, able to walk",
            age=25.0,
            target_class=cls_name
        )
        assert exp["focus_class"] == cls_name
        assert "multiclass_breakdown" in exp
        assert cls_name in exp["multiclass_breakdown"]
        assert len(exp["multiclass_breakdown"][cls_name]["top_features"]) > 0

def test_shap_global_feature_importance():
    """Verify that global SHAP feature importance aggregates over evaluation samples."""
    global_exp = shap_service.get_global_feature_importance()
    assert global_exp["status"] == "success"
    assert global_exp["sample_count"] > 0
    assert len(global_exp["global_top_features"]) >= 5
    top_feat = global_exp["global_top_features"][0]
    assert top_feat["mean_abs_shap"] > 0
    assert "feature_name" in top_feat
    assert "class_mean_impact" in top_feat

def test_shap_api_endpoints():
    """Verify explainability REST handlers directly."""
    req = ExplainabilityRequest(
        text="Severe allergic reaction after peanut ingestion, swollen tongue and throat closing",
        age=16.0,
        has_breathing_difficulty=1,
        has_anaphylaxis_symptoms=1
    )
    data = explain_incident_prediction(req)
    assert data["predicted_class"] == "CRITICAL"
    assert len(data["top_positive_features"]) > 0
    assert "clinical_disclaimer" in data

    global_data = get_global_model_explanations()
    assert "global_top_features" in global_data
    assert len(global_data["global_top_features"]) >= 5


# ---------------------------------------------------------------------------
# TEST SUITE 2: Medical Source Citation and Verification
# ---------------------------------------------------------------------------

def test_source_registry_loaded():
    """Verify source registry correctly loads all medical guidelines with metadata."""
    sources = source_registry.list_sources()
    assert len(sources) >= 8
    for s in sources:
        assert s["document_id"].startswith("kb-")
        assert len(s["document_title"]) > 5
        assert len(s["publishing_organization"]) > 0
        assert s["source_url"].startswith("http")
        assert s["review_status"] in ["Verified", "Pending Review", "Outdated", "Unavailable"]
        assert s["document_type"] in ["Clinical Guideline", "Emergency Protocol", "First Aid Manual", "Consensus Summary"]

def test_source_registry_metrics():
    """Verify source registry metrics calculation."""
    metrics = source_registry.get_source_metrics()
    assert metrics["total_sources"] >= 8
    assert metrics["verified_count"] >= 1
    assert metrics["verification_rate_pct"] > 0

def test_source_status_update():
    """Verify authorized status updates for a protocol."""
    test_doc_id = "kb-cardiac-001"
    update_payload = SourceReviewUpdateRequest(
        review_status=SourceReviewStatus.VERIFIED,
        reviewer_notes="Annual medical board re-certification",
        reviewed_by="Clinical Board Lead"
    )
    updated = source_registry.update_source_review(test_doc_id, update_payload)
    assert updated is not None
    assert updated["review_status"] == "Verified"
    assert updated["reviewer_notes"] == "Annual medical board re-certification"

def test_citation_parsing_and_grounding():
    """Verify citation tag parsing and claim support verification."""
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="kb-cardiac-001",
            document_title="AHA Adult CPR Guidelines",
            publishing_organization="American Heart Association (AHA)",
            source_name="American Heart Association (AHA)",
            source_url="https://cpr.heart.org",
            section="Adult Hands-Only CPR",
            page_number="Part 3, p. 12",
            content="Perform continuous chest compressions at 100 to 120 compressions per minute at a depth of 2 inches.",
            similarity_score=0.92
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            document_id="kb-cardiac-001",
            document_title="AHA Adult CPR Guidelines",
            publishing_organization="American Heart Association (AHA)",
            source_name="American Heart Association (AHA)",
            source_url="https://cpr.heart.org",
            section="AED Utilization",
            page_number="Part 3, p. 14",
            content="Attach the automated external defibrillator pads to the bare chest and follow voice prompts immediately.",
            similarity_score=0.88
        )
    ]

    steps = [
        {
            "action": "Perform Chest Compressions",
            "details": "Push hard and fast in the center of the chest at 100-120 compressions per minute [1]."
        },
        {
            "action": "Attach AED",
            "details": "Place automated external defibrillator pads on bare chest and allow device to analyze rhythm [2]."
        }
    ]

    citations, unsupported, summary = citation_service.verify_and_ground_citations(
        first_aid_steps=steps,
        summary_text="Cardiac arrest resuscitation following AHA protocol [1].",
        retrieved_chunks=chunks
    )

    assert len(citations) == 2
    assert citations[0].citation_index == 1
    assert citations[0].is_verified_support is True
    assert citations[0].claim_support_score > 0.40
    assert citations[1].citation_index == 2
    assert citations[1].is_verified_support is True
    assert len(unsupported) == 0
    assert summary.verification_passed is True

def test_unsupported_claim_detection():
    """Verify detection of unsupported claims citing nonexistent sources."""
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="kb-burns-004",
            document_title="WHO Burns Guidelines",
            publishing_organization="World Health Organization (WHO)",
            source_name="World Health Organization",
            section="Burn Irrigation",
            content="Cool the burn immediately with clean cool running water for 20 minutes.",
            similarity_score=0.85
        )
    ]

    steps = [
        {
            "action": "Apply Toothpaste and Ice",
            "details": "Apply butter and toothpaste directly to the skin burn [99]."
        }
    ]

    citations, unsupported, summary = citation_service.verify_and_ground_citations(
        first_aid_steps=steps,
        summary_text="Thermal burn management.",
        retrieved_chunks=chunks
    )

    assert len(unsupported) > 0
    assert any("99" in u for u in unsupported)
    assert summary.verification_passed is False

def test_sources_api_endpoints():
    """Verify medical sources API handlers directly."""
    sources = list_medical_sources()
    assert len(sources) >= 8

    metrics = get_source_registry_metrics()
    assert "total_sources" in metrics
    assert "verification_rate_pct" in metrics

    single_source = get_medical_source_by_id("kb-cardiac-001")
    assert single_source["document_id"] == "kb-cardiac-001"


# ---------------------------------------------------------------------------
# TEST SUITE 3: End-to-End System Pipeline Integration
# ---------------------------------------------------------------------------

def test_emergency_analyze_e2e_integration():
    """Verify full pipeline execution including SHAP and citation generation."""
    db = SessionLocal()
    try:
        req = EmergencyInputRequest(
            description="Patient collapsed suddenly, unresponsive, not breathing, heart stopped",
            input_type=InputTypeEnum.TEXT,
            patient_age=62
        )
        response = analyze_emergency(payload=req, db=db)
        
        assert response.priority.value == "CRITICAL"
        assert response.is_critical_bypass is True
        assert len(response.first_aid_steps) >= 1
        assert len(response.citations) >= 1
        assert response.shap_summary is not None
        assert response.shap_summary["predicted_class"] == "CRITICAL"
        assert response.evidence_verification is not None
    finally:
        db.close()
