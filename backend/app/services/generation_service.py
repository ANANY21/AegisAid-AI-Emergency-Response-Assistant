import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from ..config import settings
from ..schemas.emergency import ExtractedEmergencyInfo
from ..schemas.classification import ClassificationResult, PriorityLevel
from ..schemas.retrieval import RetrievalValidationResult, RetrievedChunk
from ..schemas.response import (
    EmergencyResponse, SystemOutcome, FirstAidStep,
    ConfidenceBreakdown, RelevanceStatus
)
from .prompt_service import SYSTEM_EMERGENCY_ROLE, build_first_aid_prompt
from ..core.logging import logger

# Deterministic medically validated fallback templates for offline / zero-key mode
DETERMINISTIC_FALLBACKS = {
    "cardiac_arrest": {
        "summary": "Suspected sudden cardiac arrest or unresponsiveness. Immediate CPR required.",
        "steps": [
            FirstAidStep(
                step_number=1,
                action="Call 911 / 112 immediately",
                details="Request an ambulance and ask for an Automated External Defibrillator (AED).",
                caution="Do not leave the patient unattended if other bystanders can make the call.",
                visual_guide_key="cpr"
            ),
            FirstAidStep(
                step_number=2,
                action="Begin Hands-Only CPR",
                details="Place heels of interlocked hands in center of chest. Push hard and fast at 100-120 compressions/min, at least 2 inches deep. Allow complete recoil.",
                caution="Push in the center of the chest without stopping until EMS arrives or AED is attached.",
                visual_guide_key="cpr"
            )
        ],
        "precautions": ["Ensure casualty is on a firm flat surface", "Do not delay compressions for pulse checks"],
        "what_to_avoid": ["Do NOT stop compressions for more than 10 seconds", "Do NOT give breaths if untrained"],
        "when_to_seek": "Immediately. Sudden cardiac arrest is an absolute life-or-death emergency."
    },
    "choking": {
        "summary": "Acute severe airway obstruction (choking). Immediate physical dislodgement required.",
        "steps": [
            FirstAidStep(
                step_number=1,
                action="Deliver 5 Back Blows",
                details="Lean the person forward, supporting their chest with one hand. Deliver up to 5 sharp blows between shoulder blades with the heel of your hand.",
                caution="Stop immediately if the obstruction is expelled.",
                visual_guide_key="heimlich"
            ),
            FirstAidStep(
                step_number=2,
                action="Perform 5 Abdominal Thrusts (Heimlich)",
                details="Stand behind victim, wrap arms around waist. Place thumb side of fist just above navel, grasp with other hand, pull sharply inward and upward.",
                caution="Do not perform abdominal thrusts on infants under 1 year or pregnant women (use chest thrusts).",
                visual_guide_key="heimlich"
            )
        ],
        "precautions": ["Alternate 5 back blows and 5 abdominal thrusts", "If victim goes limp, begin CPR immediately"],
        "what_to_avoid": ["Do NOT perform blind finger sweeps", "Do NOT pat them lightly on the back while upright"],
        "when_to_seek": "Immediately if obstruction is not cleared in 30 seconds or if consciousness is lost."
    },
    "severe_bleeding": {
        "summary": "High-volume external hemorrhage. Immediate pressure and hemorrhage control required.",
        "steps": [
            FirstAidStep(
                step_number=1,
                action="Apply Firm Continuous Direct Pressure",
                details="Place a clean cloth, sterile gauze, or gloved hand directly over bleeding site. Lean your body weight firmly onto the wound.",
                caution="Do not remove the cloth if blood soaks through; add more layers on top.",
                visual_guide_key="pressure_bandage"
            ),
            FirstAidStep(
                step_number=2,
                action="Apply Tourniquet if Bleeding is Uncontrolled on Limb",
                details="Place commercial windlass tourniquet 2-3 inches above the wound on arm or leg (never over a joint). Tighten until bleeding stops.",
                caution="Record the exact time tourniquet was applied. Never loosen it yourself.",
                visual_guide_key="pressure_bandage"
            )
        ],
        "precautions": ["Keep patient lying down and calm", "Cover with blanket to prevent hypothermic shock"],
        "what_to_avoid": ["Do NOT remove deeply embedded objects (tamponade around them)", "Do NOT use narrow wire or string as a tourniquet"],
        "when_to_seek": "Immediately. Heavy arterial or venous bleeding can cause hemorrhagic shock within minutes."
    },
    "burn": {
        "summary": "Thermal or scald burn. Immediate cool water irrigation required.",
        "steps": [
            FirstAidStep(
                step_number=1,
                action="Cool Under Running Tap Water for 20 Minutes",
                details="Hold burn under clean, cool running water (not ice) for at least 20 continuous minutes. This stops thermal progression.",
                caution="Never apply ice, ice water, butter, oil, or toothpaste to a burn.",
                visual_guide_key="burns_water"
            ),
            FirstAidStep(
                step_number=2,
                action="Cover Loosely with Clean Plastic Wrap or Sterile Dressing",
                details="After 20 minutes of cooling, remove jewelry before swelling. Cover loosely with cling film layers to shield nerves and prevent infection.",
                caution="Do not wrap tightly around limbs.",
                visual_guide_key="burns_water"
            )
        ],
        "precautions": ["Keep the rest of the patient warm", "Gently elevate burned limb if possible"],
        "what_to_avoid": ["Do NOT pop burn blisters", "Do NOT pull off clothing stuck to the burn"],
        "when_to_seek": "Seek emergency care if burn is larger than patient's palm, on face/hands/genitals, or charred white."
    },
    "stroke": {
        "summary": "Suspected acute neurological event (stroke). Immediate BE-FAST protocol required.",
        "steps": [
            FirstAidStep(
                step_number=1,
                action="Call 911 Immediately and Record Exact Symptom Time",
                details="Call emergency services and state suspected stroke. Record the exact minute symptoms were first observed for medication eligibility.",
                caution="Every minute delays critical clot-busting therapy.",
                visual_guide_key="recovery_position"
            ),
            FirstAidStep(
                step_number=2,
                action="Position in Comfortable Recovery Position",
                details="Keep patient lying down with head and shoulders slightly elevated. If drowsy or vomiting, place in the lateral recovery position.",
                caution="Do not give food, water, or aspirin before hospital evaluation.",
                visual_guide_key="recovery_position"
            )
        ],
        "precautions": ["Keep patient quiet and calm", "Monitor airway and breathing constantly"],
        "what_to_avoid": ["Do NOT give aspirin (stroke could be hemorrhagic)", "Do NOT give anything by mouth"],
        "when_to_seek": "Immediately. Acute stroke treatments have a strict 3-to-4.5-hour time window."
    }
}

class EmergencyGenerationService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    def _call_groq_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Executes inference against Groq API with robust error handling and timeout safety.
        """
        if not self.groq_api_key:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_EMERGENCY_ROLE},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }
        
        try:
            with httpx.Client(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
                resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                elif resp.status_code == 429:
                    logger.warning("Groq API rate limit encountered. Falling back to deterministic medical protocol.")
                else:
                    logger.warning(f"Groq API returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            
        return None

    def generate_response(
        self,
        session_id: str,
        raw_description: str,
        extracted_info: ExtractedEmergencyInfo,
        classification: ClassificationResult,
        retrieval_val: RetrievalValidationResult,
        safety_evaluation: Dict[str, Any]
    ) -> EmergencyResponse:
        """
        Generates grounded, structured emergency response based on system outcome,
        safety rules, and validated retrieval evidence.
        """
        outcome = safety_evaluation["outcome"]
        is_critical = safety_evaluation.get("is_critical_bypass", False)
        immediate_warning = safety_evaluation.get("immediate_emergency_warning")
        confidence_breakdown = safety_evaluation["confidence_breakdown"]
        clarification_questions = safety_evaluation.get("clarification_questions", [])
        
        sources_meta = []
        for c in retrieval_val.top_chunks:
            sources_meta.append({
                "source_name": c.source_name,
                "document_title": c.document_title,
                "section": c.section,
                "source_url": c.source_url,
                "publication_date": c.publication_date,
                "relevance_score": c.similarity_score
            })

        # Scenario 1: Ambiguous Input -> Withhold medical instructions, ask clarifying questions
        if outcome == SystemOutcome.AMBIGUOUS_INPUT:
            return EmergencyResponse(
                session_id=session_id,
                outcome=outcome,
                priority=classification.priority,
                is_critical_bypass=False,
                immediate_emergency_warning=None,
                summary="The emergency description is too brief or ambiguous to determine appropriate medical triage safely.",
                first_aid_steps=[
                    FirstAidStep(
                        step_number=1,
                        action="Assess Patient Responsiveness",
                        details="Check if the person can hear you, speak, or squeeze your hand.",
                        caution="Do not shake vigorously.",
                        visual_guide_key=None
                    )
                ],
                precautions=["Do not give medications without knowing the underlying condition"],
                what_to_avoid=["Do not assume the situation is mild if symptoms change rapidly"],
                when_to_seek_immediate_care="If breathing becomes difficult, chest pain arises, or consciousness wavers, call emergency services immediately.",
                sources=[],
                confidence_breakdown=confidence_breakdown,
                clarification_questions=clarification_questions,
                generated_at=datetime.utcnow().isoformat(),
                llm_provider="Safety Rule Engine (Ambiguity Guardrail)"
            )

        # Scenario 2: Low Retrieval Relevance -> Reject context, withhold speculative advice
        if outcome == SystemOutcome.LOW_RETRIEVAL_RELEVANCE:
            return EmergencyResponse(
                session_id=session_id,
                outcome=outcome,
                priority=classification.priority,
                is_critical_bypass=False,
                immediate_emergency_warning=immediate_warning,
                summary=(
                    "No verified medical protocols in our trusted knowledge base met the strict relevance threshold "
                    f"for this scenario ({retrieval_val.rejection_reason}). To ensure safety, unsupported guidance is withheld."
                ),
                first_aid_steps=[
                    FirstAidStep(
                        step_number=1,
                        action="Seek Professional Medical Assessment",
                        details="Contact a local clinic, doctor, or emergency department for a certified clinical evaluation.",
                        caution="Do not rely on unverified internet remedies.",
                        visual_guide_key=None
                    )
                ],
                precautions=["Keep patient quiet, calm, and monitored", "Record any evolving symptoms"],
                what_to_avoid=["Do NOT attempt experimental or non-prescribed treatments"],
                when_to_seek_immediate_care="If any red flags occur (loss of consciousness, breathing difficulty, extreme pain, or numbness).",
                sources=[],
                confidence_breakdown=confidence_breakdown,
                clarification_questions=clarification_questions,
                generated_at=datetime.utcnow().isoformat(),
                llm_provider="Safety Rule Engine (Relevance Threshold Escalation)"
            )

        # Scenario 3: Conflicting Information -> Escalate to human care
        if outcome == SystemOutcome.CONFLICTING_INFORMATION:
            return EmergencyResponse(
                session_id=session_id,
                outcome=outcome,
                priority=classification.priority,
                is_critical_bypass=False,
                immediate_emergency_warning=immediate_warning,
                summary="Conflicting clinical treatment protocols were identified. To avoid contraindicated actions, treatment guidance has been halted.",
                first_aid_steps=[
                    FirstAidStep(
                        step_number=1,
                        action="Contact Healthcare Professional or Nurse Triage",
                        details="Speak directly to emergency dispatchers or a medical hotline to clarify the safest procedure.",
                        caution="Opposing actions may worsen the underlying injury.",
                        visual_guide_key=None
                    )
                ],
                precautions=["Do not administer oral medications", "Keep the patient still and resting"],
                what_to_avoid=["Do not follow conflicting home advice"],
                when_to_seek_immediate_care="Seek urgent in-person care at an emergency facility immediately.",
                sources=sources_meta,
                confidence_breakdown=confidence_breakdown,
                clarification_questions=[],
                generated_at=datetime.utcnow().isoformat(),
                llm_provider="Safety Rule Engine (Conflict Guardrail)"
            )

        # Scenario 4: Grounded Response Generation (Groq API or Deterministic Protocol)
        groq_result = None
        if self.groq_api_key:
            prompt = build_first_aid_prompt(
                raw_description=raw_description,
                extracted_info=extracted_info,
                classification=classification,
                evidence_chunks=retrieval_val.top_chunks
            )
            groq_result = self._call_groq_api(prompt)

        if groq_result and "first_aid_steps" in groq_result:
            steps = []
            for s in groq_result.get("first_aid_steps", []):
                steps.append(FirstAidStep(
                    step_number=s.get("step_number", len(steps)+1),
                    action=s.get("action", "Follow protocol"),
                    details=s.get("details", ""),
                    caution=s.get("caution"),
                    visual_guide_key=s.get("visual_guide_key")
                ))
            summary = groq_result.get("summary", "Emergency assessment based on verified medical protocols.")
            precautions = groq_result.get("precautions", ["Keep the casualty calm and monitored."])
            what_to_avoid = groq_result.get("what_to_avoid", ["Avoid unprescribed medication."])
            when_to_seek = groq_result.get("when_to_seek_immediate_care", "If symptoms worsen or do not rapidly improve, call emergency services.")
            provider_label = f"Groq ({self.model})"
        else:
            # High-fidelity deterministic fallback based on extracted incident
            mapped = DETERMINISTIC_FALLBACKS.get(extracted_info.incident_type)
            if not mapped:
                # Find best matching fallback
                if "chok" in raw_description.lower():
                    mapped = DETERMINISTIC_FALLBACKS["choking"]
                elif "bleed" in raw_description.lower() or "cut" in raw_description.lower():
                    mapped = DETERMINISTIC_FALLBACKS["severe_bleeding"]
                elif "burn" in raw_description.lower() or "scald" in raw_description.lower():
                    mapped = DETERMINISTIC_FALLBACKS["burn"]
                elif "stroke" in raw_description.lower() or "droop" in raw_description.lower():
                    mapped = DETERMINISTIC_FALLBACKS["stroke"]
                else:
                    mapped = DETERMINISTIC_FALLBACKS["cardiac_arrest"] if is_critical else DETERMINISTIC_FALLBACKS["severe_bleeding"]

            summary = mapped["summary"]
            steps = mapped["steps"]
            precautions = mapped["precautions"]
            what_to_avoid = mapped["what_to_avoid"]
            when_to_seek = mapped["when_to_seek"]
            provider_label = "Deterministic Medical Protocol (AegisAid Core Engine)"

        return EmergencyResponse(
            session_id=session_id,
            outcome=outcome,
            priority=classification.priority,
            is_critical_bypass=is_critical,
            immediate_emergency_warning=immediate_warning,
            emergency_service_number="911 / 112 / 999 / 108",
            summary=summary,
            first_aid_steps=steps,
            precautions=precautions,
            what_to_avoid=what_to_avoid,
            when_to_seek_immediate_care=when_to_seek,
            sources=sources_meta,
            confidence_breakdown=confidence_breakdown,
            clarification_questions=clarification_questions,
            generated_at=datetime.utcnow().isoformat(),
            llm_provider=provider_label
        )

# Singleton generation service
generation_service = EmergencyGenerationService()
