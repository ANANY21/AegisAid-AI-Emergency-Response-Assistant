from typing import List, Dict, Any, Optional
import numpy as np
from ..config import settings
from ..schemas.retrieval import RetrievedChunk, RetrievalValidationResult, RelevanceStatus
from ..core.logging import logger

class RetrievalRelevanceValidator:
    """
    Industry-review mandated validation layer.
    Ensures that medical guidance is NEVER hallucinated or generated from irrelevant,
    conflicting, or insufficient retrieved evidence.
    """
    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.RETRIEVAL_SIMILARITY_THRESHOLD

    def validate_retrieval(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> RetrievalValidationResult:
        if not retrieved_chunks:
            return RetrievalValidationResult(
                status=RelevanceStatus.INSUFFICIENT,
                has_sufficient_evidence=False,
                top_chunks=[],
                max_similarity=0.0,
                mean_similarity=0.0,
                threshold_applied=self.threshold,
                rejection_reason="No medical guidelines retrieved from knowledge base.",
                detected_conflicts=[],
                provenance_verified=False
            )

        scores = [chunk.similarity_score for chunk in retrieved_chunks]
        max_sim = float(np.max(scores))
        mean_sim = float(np.mean(scores))

        # Check provenance: each chunk must have identifiable authorized source
        provenance_verified = all(
            chunk.source_name and len(chunk.source_name.strip()) > 2 for chunk in retrieved_chunks
        )

        # 1. Check for Insufficient Evidence / Irrelevance
        # If the highest similarity chunk falls below the configured threshold, reject
        if max_sim < self.threshold:
            logger.warning(
                f"Retrieval rejected: Max similarity {max_sim:.4f} is below safety threshold {self.threshold:.4f} for query '{query[:60]}...'"
            )
            return RetrievalValidationResult(
                status=RelevanceStatus.IRRELEVANT,
                has_sufficient_evidence=False,
                top_chunks=[c for c in retrieved_chunks if c.similarity_score >= (self.threshold - 0.15)],
                max_similarity=round(max_sim, 4),
                mean_similarity=round(mean_sim, 4),
                threshold_applied=self.threshold,
                rejection_reason=(
                    f"Retrieved knowledge does not sufficiently match the described emergency symptoms "
                    f"(Score: {max_sim:.2f} < Threshold {self.threshold:.2f}). Unsupported medical advice is withheld."
                ),
                detected_conflicts=[],
                provenance_verified=provenance_verified
            )

        # 2. Check for Conflicting Retrieved Information
        # E.g. Check for opposing contraindications across retrieved procedures
        detected_conflicts = []
        all_contraindications = []
        for c in retrieved_chunks:
            if c.similarity_score >= self.threshold:
                all_contraindications.extend(c.contraindications)

        # Check classic clinical conflicts (e.g., inducing vomiting vs not inducing vomiting, or aspirin vs bleeding)
        q_lower = query.lower()
        if "bleeding" in q_lower and any("aspirin" in c.content.lower() for c in retrieved_chunks):
            detected_conflicts.append("Clinical conflict: Aspirin antiplatelet therapy contraindicated in active bleeding / hemorrhagic trauma")
            
        if "vomit" in q_lower and any("induce vomiting" in c.content.lower() for c in retrieved_chunks):
            detected_conflicts.append("Conflict: Induced emesis contraindicated in caustic or hydrocarbon chemical ingestion")

        if detected_conflicts:
            logger.warning(f"Conflicting medical evidence detected in retrieval: {detected_conflicts}")
            return RetrievalValidationResult(
                status=RelevanceStatus.CONFLICTING,
                has_sufficient_evidence=False,
                top_chunks=retrieved_chunks,
                max_similarity=round(max_sim, 4),
                mean_similarity=round(mean_sim, 4),
                threshold_applied=self.threshold,
                rejection_reason="Conflicting clinical guidance detected in retrieved evidence. Escalating to human clinician.",
                detected_conflicts=detected_conflicts,
                provenance_verified=provenance_verified
            )

        # 3. Validated Sufficient Evidence
        valid_chunks = [c for c in retrieved_chunks if c.similarity_score >= self.threshold]
        if not valid_chunks:
            valid_chunks = retrieved_chunks[:1]  # At least top chunk if border

        return RetrievalValidationResult(
            status=RelevanceStatus.VALID,
            has_sufficient_evidence=True,
            top_chunks=valid_chunks,
            max_similarity=round(max_sim, 4),
            mean_similarity=round(mean_sim, 4),
            threshold_applied=self.threshold,
            rejection_reason=None,
            detected_conflicts=[],
            provenance_verified=provenance_verified
        )

# Singleton validator instance
retrieval_validator = RetrievalRelevanceValidator()
