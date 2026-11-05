import json
from typing import Dict, Any, List
from ..schemas.emergency import ExtractedEmergencyInfo
from ..schemas.retrieval import RetrievedChunk
from ..schemas.classification import ClassificationResult

SYSTEM_EMERGENCY_ROLE = """You are AegisAid's Clinical Response Engine, an expert healthcare decision-support system.
YOUR STRICT MANDATES:
1. Ground every medical instruction ONLY in the provided verified evidence. NEVER invent or hallucinate first-aid steps or treatments.
2. State all actions in clear, direct, step-by-step imperative voice (e.g. "Step 1: Apply direct pressure").
3. Include critical contraindications (what NOT to do) to prevent user harm.
4. Always state uncertainty when information is incomplete. Never state a definitive medical diagnosis.
5. Emphasize that you are an AI decision-support assistant and not a replacement for emergency medical personnel.
6. Provide output in strict JSON format conforming to the requested schema.
"""

def build_first_aid_prompt(
    raw_description: str,
    extracted_info: ExtractedEmergencyInfo,
    classification: ClassificationResult,
    evidence_chunks: List[RetrievedChunk]
) -> str:
    """
    Constructs an evidence-grounded prompt for first-aid instruction generation.
    """
    evidence_text = "\n\n".join([
        f"--- EVIDENCE SOURCE [{idx+1}]: {c.document_title} ({c.source_name}) ---\n"
        f"SECTION: {c.section}\n"
        f"CONTENT: {c.content}\n"
        f"CONTRAINDICATIONS: {', '.join(c.contraindications) if c.contraindications else 'None listed'}"
        for idx, c in enumerate(evidence_chunks)
    ])
    
    prompt = f"""[EMERGENCY INCIDENT DATA]
- User Description: "{raw_description}"
- Priority Level: {classification.priority.value} (Confidence: {classification.confidence})
- Extracted Symptoms: {', '.join(extracted_info.symptoms)}
- Affected Body Parts: {', '.join(extracted_info.affected_body_parts)}
- Patient Age: {extracted_info.age if extracted_info.age is not None else 'Unknown'}
- Duration: {extracted_info.duration}

[VERIFIED RETRIEVED MEDICAL EVIDENCE]
{evidence_text if evidence_chunks else "NO VERIFIED EVIDENCE AVAILABLE. DO NOT INVENT MEDICAL TREATMENTS."}

[TASK]
Generate a grounded, actionable emergency response adhering strictly to the retrieved evidence above.
Return ONLY valid JSON matching this exact structure:
{{
  "summary": "Concise 1-2 sentence emergency situation summary",
  "first_aid_steps": [
    {{
      "step_number": 1,
      "action": "Brief action heading",
      "details": "Step-by-step instruction grounded in evidence",
      "caution": "Immediate caution or safety warning if applicable",
      "visual_guide_key": "cpr" | "heimlich" | "pressure_bandage" | "burns_water" | "recovery_position" | null
    }}
  ],
  "precautions": ["Key precautions based on the evidence"],
  "what_to_avoid": ["Actions that must NOT be taken, e.g. do not pop blisters, do not give water if choking"],
  "when_to_seek_immediate_care": "Clear criteria for when symptoms mandate urgent hospital transport"
}}
"""
    return prompt

def build_clarification_prompt(
    raw_description: str,
    extracted_info: ExtractedEmergencyInfo,
    missing_items: List[str]
) -> str:
    return f"""[INCIDENT DATA]
User statement: "{raw_description}"
Missing clinical parameters: {', '.join(missing_items)}

[TASK]
Explain politely that the description lacks critical details for safe triage.
Ask 2 to 3 targeted clarification questions to understand whether there is immediate danger.
Return valid JSON:
{{
  "summary": "We need more information to assess this situation safely.",
  "clarification_questions": ["Question 1", "Question 2"],
  "safe_immediate_advice": "If the person has severe pain, difficulty breathing, or bleeding, contact emergency services immediately."
}}
"""
