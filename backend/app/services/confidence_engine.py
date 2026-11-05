from typing import Dict, Any, List, Optional
from ..schemas.emergency import ExtractedEmergencyInfo
from ..schemas.classification import ClassificationResult, PriorityLevel
from ..schemas.retrieval import RetrievalValidationResult, RelevanceStatus
from ..schemas.response import SystemOutcome, ConfidenceBreakdown
from ..config import settings
from ..core.logging import logger

class ConfidenceAndSafetyEngine:
    """
    Central Safety & Controlled Escalation Layer.
    Orchestrates deterministic safety rules, decouples ML classifier confidence from
    retrieval relevance and response faithfulness, and enforces immediate emergency bypass.
    """
    def __init__(
        self,
        classifier_confidence_threshold: float = None,
        retrieval_relevance_threshold: float = None
    ):
        self.clf_threshold = classifier_confidence_threshold or settings.CLASSIFIER_CONFIDENCE_THRESHOLD
        self.ret_threshold = retrieval_relevance_threshold or settings.RETRIEVAL_SIMILARITY_THRESHOLD

    def evaluate_safety_and_escalation(
        self,
        extracted_info: ExtractedEmergencyInfo,
        classification: ClassificationResult,
        retrieval_val: RetrievalValidationResult,
        raw_text: str
    ) -> Dict[str, Any]:
        """
        Determines the system outcome (A through E) and constructs safety guardrails.
        """
        reasons = []
        
        # 1. OUTCOME E: CRITICAL EMERGENCY (Immediate Life-Threatening Bypass)
        # Never delay emergency response if life-threatening indicators or CRITICAL priority
        if classification.is_critical or extracted_info.is_life_threatening:
            logger.warning(f"CRITICAL EMERGENCY BYPASS TRIGGERED: {classification.decision_factors}")
            return {
                "outcome": SystemOutcome.CRITICAL_EMERGENCY,
                "is_critical_bypass": True,
                "immediate_emergency_warning": (
                    "CRITICAL EMERGENCY ALERT: High-risk, life-threatening symptoms detected. "
                    "Immediately call 911 / 112 / 999 or your local emergency dispatch. "
                    "Do NOT delay to read extended instructions."
                ),
                "confidence_breakdown": ConfidenceBreakdown(
                    classifier_confidence=classification.confidence,
                    retrieval_relevance_score=retrieval_val.max_similarity,
                    faithfulness_score=1.0,
                    relevance_status=retrieval_val.status
                ),
                "escalation_reason": "Life-threatening clinical indicators detected requiring immediate emergency medical dispatch.",
                "clarification_questions": []
            }

        # 2. OUTCOME B: AMBIGUOUS INPUT / MISSING CRITICAL INFORMATION
        # If user input is too sparse (e.g. 1-2 vague words like 'hurt' or 'sick')
        words = raw_text.strip().split()
        is_too_vague = len(words) < 3 or (
            extracted_info.incident_type == "unknown_emergency"
            and len(extracted_info.symptoms) == 1
            and extracted_info.symptoms[0] == "unspecified acute distress"
        )
        
        if is_too_vague and not classification.is_critical:
            logger.info("Ambiguous input detected; escalating to clarification mode.")
            return {
                "outcome": SystemOutcome.AMBIGUOUS_INPUT,
                "is_critical_bypass": False,
                "immediate_emergency_warning": None,
                "confidence_breakdown": ConfidenceBreakdown(
                    classifier_confidence=classification.confidence,
                    retrieval_relevance_score=retrieval_val.max_similarity,
                    faithfulness_score=0.90,
                    relevance_status=retrieval_val.status
                ),
                "escalation_reason": "Emergency description lacks sufficient clinical details for safe guidance.",
                "clarification_questions": extracted_info.missing_information or [
                    "What specific symptoms is the person experiencing?",
                    "Is the person conscious and able to respond to you?",
                    "Are there any visible injuries, bleeding, or breathing difficulties?"
                ]
            }

        # 3. OUTCOME D: CONFLICTING RETRIEVED INFORMATION
        if retrieval_val.status == RelevanceStatus.CONFLICTING:
            logger.warning("Conflicting retrieved medical knowledge detected.")
            return {
                "outcome": SystemOutcome.CONFLICTING_INFORMATION,
                "is_critical_bypass": False,
                "immediate_emergency_warning": (
                    "CAUTION: Conflicting medical protocols detected for these symptoms. "
                    "To prevent injury, do not attempt unverified interventions. Contact a physician or urgent care."
                ),
                "confidence_breakdown": ConfidenceBreakdown(
                    classifier_confidence=classification.confidence,
                    retrieval_relevance_score=retrieval_val.max_similarity,
                    faithfulness_score=0.75,
                    relevance_status=retrieval_val.status
                ),
                "escalation_reason": f"Conflicting medical evidence: {', '.join(retrieval_val.detected_conflicts)}",
                "clarification_questions": []
            }

        # 4. OUTCOME C: LOW RETRIEVAL RELEVANCE (Industry Review Requirement)
        # If retrieved documents fail the relevance threshold, reject and escalate
        if not retrieval_val.has_sufficient_evidence or retrieval_val.status == RelevanceStatus.IRRELEVANT:
            logger.info("Low retrieval relevance; safely withholding unsupported guidance.")
            return {
                "outcome": SystemOutcome.LOW_RETRIEVAL_RELEVANCE,
                "is_critical_bypass": False,
                "immediate_emergency_warning": (
                    "NOTICE: Verified first-aid guidance could not be matched with high confidence to this specific scenario. "
                    "To avoid harm, speculative medical guidance is withheld. Please consult medical professionals."
                ),
                "confidence_breakdown": ConfidenceBreakdown(
                    classifier_confidence=classification.confidence,
                    retrieval_relevance_score=retrieval_val.max_similarity,
                    faithfulness_score=0.60,
                    relevance_status=retrieval_val.status
                ),
                "escalation_reason": retrieval_val.rejection_reason or "Retrieved knowledge below relevance threshold.",
                "clarification_questions": [
                    "Can you clarify the cause of the injury or symptom?",
                    "Are you able to speak directly to a local nurse triage hotline?"
                ]
            }

        # 5. OUTCOME A: SUFFICIENT EVIDENCE
        # Safe to proceed with grounded generation
        return {
            "outcome": SystemOutcome.SUFFICIENT_EVIDENCE,
            "is_critical_bypass": False,
            "immediate_emergency_warning": None,
            "confidence_breakdown": ConfidenceBreakdown(
                classifier_confidence=classification.confidence,
                retrieval_relevance_score=retrieval_val.max_similarity,
                faithfulness_score=0.98,
                relevance_status=retrieval_val.status
            ),
            "escalation_reason": None,
            "clarification_questions": []
        }

# Singleton instance
safety_engine = ConfidenceAndSafetyEngine()
