import re
from typing import Dict, Any, List, Optional
from ..schemas.emergency import ExtractedEmergencyInfo, InputTypeEnum
from ..core.logging import logger

BODY_PARTS = [
    "head", "chest", "throat", "neck", "arm", "shoulder", "wrist", "hand", "finger",
    "abdomen", "stomach", "back", "pelvis", "groin", "leg", "thigh", "knee", "ankle",
    "foot", "toe", "eye", "mouth", "tongue", "face"
]

SYMPTOM_PATTERNS = {
    "difficulty breathing": [r"can'?t breathe", r"shortness of breath", r"gasping", r"wheezing", r"stridor", r"breathless"],
    "chest pain": [r"chest pain", r"chest pressure", r"crushing chest", r"angina", r"squeezing chest"],
    "unconsciousness": [r"unconscious", r"passed out", r"fainted", r"unresponsive", r"collapsed"],
    "severe bleeding": [r"spurting blood", r"bleeding heavily", r"blood everywhere", r"soaking through", r"arterial bleed"],
    "choking": [r"choking", r"cannot talk", r"swallowed object", r"clutching throat"],
    "seizure": [r"seizure", r"convulsing", r"shaking uncontrollably", r"epileptic fit"],
    "facial droop": [r"face droop", r"drooping eye", r"crooked smile"],
    "slurred speech": [r"slurred speech", r"cannot speak clearly", r"muffled words"],
    "swelling": [r"swollen", r"swelling", r"puffed up", r"angioedema"],
    "burn": [r"burn\w*", r"scald\w*", r"blister\w*", r"charred skin", r"boiling\s+water"]
}

INCIDENT_MAPPING = {
    "cardiac_arrest": ["not breathing", "unresponsive", "cardiac arrest", "heart stopped", "no pulse"],
    "heart_attack": ["chest pain", "crushing", "arm pain", "jaw pain", "sweating"],
    "choking": ["choking", "food stuck", "throat blocked", "strangling"],
    "severe_bleeding": ["bleeding", "cut", "stab", "laceration", "wound", "spurting"],
    "stroke": ["stroke", "face droop", "slurred speech", "arm weakness", "be fast"],
    "anaphylaxis": ["allergy", "peanut", "bee sting", "swollen tongue", "hives", "stridor"],
    "burn": ["burn", "scald", "boiling water", "fire", "hot oil"],
    "seizure": ["seizure", "convulsion", "epilepsy"],
    "overdose": ["overdose", "pinpoint pupils", "pills", "poisoning", "chemical"]
}

def extract_emergency_information(
    text: str,
    input_type: str = "text",
    patient_age: Optional[int] = None,
    duration: Optional[str] = None,
    location_text: Optional[str] = None
) -> ExtractedEmergencyInfo:
    """
    Extracts structured emergency information following medical triage protocols.
    Identifies what critical clinical data is missing without hallucinating values.
    """
    text_lower = text.lower()
    
    # 1. Detect symptoms
    extracted_symptoms: List[str] = []
    for symptom, patterns in SYMPTOM_PATTERNS.items():
        for pat in patterns:
            if re.search(r"\b" + pat + r"\b", text_lower):
                extracted_symptoms.append(symptom)
                break
                
    # 2. Detect affected body parts
    affected_body_parts: List[str] = []
    for bp in BODY_PARTS:
        if re.search(r"\b" + bp + r"(s)?\b", text_lower):
            affected_body_parts.append(bp)
            
    # 3. Detect clinical severity indicators
    severity_indicators: List[str] = []
    if any(s in extracted_symptoms for s in ["unconsciousness", "choking"]):
        severity_indicators.append("Compromised airway or consciousness")
    if "difficulty breathing" in extracted_symptoms:
        severity_indicators.append("Respiratory distress")
    if "chest pain" in extracted_symptoms:
        severity_indicators.append("Potential acute coronary syndrome")
    if "severe bleeding" in extracted_symptoms:
        severity_indicators.append("Critical hemorrhage")
    if "facial droop" in extracted_symptoms or "slurred speech" in extracted_symptoms:
        severity_indicators.append("Acute neurological deficit (possible stroke)")

    # 4. Map to incident type
    incident_type = "unknown_emergency"
    for inc_name, keywords in INCIDENT_MAPPING.items():
        if any(kw in text_lower for kw in keywords):
            incident_type = inc_name
            break

    # 5. Extract duration if present in text and not provided
    extracted_duration = duration or "unknown"
    if extracted_duration == "unknown":
        duration_match = re.search(r"\b(\d+)\s*(minute|min|hour|hr|day|sec)s?\b", text_lower)
        if duration_match:
            extracted_duration = f"{duration_match.group(1)} {duration_match.group(2)}s"

    # 6. Extract age if present in text and not provided
    extracted_age = patient_age
    if extracted_age is None:
        age_match = re.search(r"\b(\d{1,3})\s*(?:year|yr)s?\s*(?:old)?\b", text_lower)
        if age_match:
            try:
                extracted_age = int(age_match.group(1))
            except ValueError:
                pass

    # 7. Check for life-threatening status
    is_life_threatening = bool(
        "unconsciousness" in extracted_symptoms
        or "choking" in extracted_symptoms
        or "severe bleeding" in extracted_symptoms
        or "cardiac_arrest" in incident_type
        or "stroke" in incident_type
    )

    # 8. Identify missing clinical information for triage safety
    missing_info = []
    if "unconsciousness" not in extracted_symptoms and "conscious" not in text_lower:
        missing_info.append("Is the patient currently alert and conscious?")
    if "difficulty breathing" not in extracted_symptoms and "breathing" not in text_lower:
        missing_info.append("Is the patient breathing normally without wheezing or gasping?")
    if extracted_duration == "unknown":
        missing_info.append("Approximately how long ago did symptoms start?")
    if extracted_age is None:
        missing_info.append("What is the patient's approximate age?")

    return ExtractedEmergencyInfo(
        incident_type=incident_type,
        symptoms=extracted_symptoms or ["unspecified acute distress"],
        affected_body_parts=affected_body_parts or ["general/unspecified"],
        severity_indicators=severity_indicators,
        duration=extracted_duration,
        age=extracted_age,
        location=location_text or "unspecified",
        input_type=input_type,
        missing_information=missing_info,
        is_life_threatening=is_life_threatening
    )
