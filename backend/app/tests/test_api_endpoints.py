import pytest
from app.main import health_check
from app.api.emergency import analyze_emergency
from app.api.hospitals import get_nearby_hospitals
from app.api.evaluation import get_benchmark_report
from app.schemas.emergency import EmergencyInputRequest, InputTypeEnum
from app.database.connection import SessionLocal

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_health_check_controller():
    data = health_check()
    assert data["status"] == "healthy"
    assert data["knowledge_base_chunks_loaded"] > 0
    assert data["safety_guardrails_active"] is True

def test_critical_emergency_controller(db_session):
    payload = EmergencyInputRequest(
        description="Patient collapsed, unresponsive, not breathing, turning blue",
        input_type=InputTypeEnum.TEXT,
        patient_age=60,
        duration="2 minutes"
    )
    response = analyze_emergency(payload=payload, db=db_session)
    assert response.priority == "CRITICAL"
    assert response.outcome == "CRITICAL_EMERGENCY"
    assert response.is_critical_bypass is True
    assert response.immediate_emergency_warning is not None
    assert len(response.first_aid_steps) > 0

def test_burn_first_aid_controller(db_session):
    payload = EmergencyInputRequest(
        description="Spilled boiling water on hand and forearm, skin is red and blistering with severe stinging",
        input_type=InputTypeEnum.TEXT,
        patient_age=28,
        duration="5 minutes"
    )
    response = analyze_emergency(payload=payload, db=db_session)
    assert response.priority in ["HIGH", "MODERATE"]
    assert any("cool" in step.action.lower() or "water" in step.details.lower() for step in response.first_aid_steps)

def test_hospitals_nearby_controller():
    data = get_nearby_hospitals(lat=37.7749, lng=-122.4194)
    assert data.count > 0
    assert len(data.facilities) > 0
    assert "disclaimer" in data.model_dump()

def test_evaluation_report_controller(db_session):
    report = get_benchmark_report(db=db_session)
    assert report.classification_metrics.critical_class_recall > 0.70
    assert report.retrieval_metrics.precision_at_k > 0.80
    assert report.safety_escalation_metrics.total_incidents_processed > 0
