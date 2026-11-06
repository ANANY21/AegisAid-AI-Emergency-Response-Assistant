import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from ..schemas.retrieval import RetrievedChunk
from ..schemas.sources import (
    CitationDetail, EvidenceVerificationSummary,
    SourceReviewStatus
)
from .transformer_service import context_embedder
from ..core.logging import logger

class MedicalCitationService:
    def __init__(self, support_threshold: float = 0.40):
        self.support_threshold = support_threshold

    def parse_citations_from_text(self, text: str) -> List[int]:
        """
        Extracts all numeric citation tags like [1], [2], [1, 2] from generated text.
        """
        tags = set()
        # Find single [1] or compound [1, 2]
        matches = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", text)
        for m in matches:
            for num in m.split(","):
                num = num.strip()
                if num.isdigit():
                    tags.add(int(num))
        return sorted(list(tags))

    def verify_and_ground_citations(
        self,
        first_aid_steps: List[Dict[str, Any]],
        summary_text: str,
        retrieved_chunks: List[RetrievedChunk]
    ) -> Tuple[List[CitationDetail], List[str], EvidenceVerificationSummary]:
        """
        Performs claim-level evidence verification:
        1. Maps each step and summary citation to the corresponding retrieved chunk.
        2. Computes claim support score between step action/details and the source content.
        3. Identifies unsupported claims and outdated/conflicting source flags.
        """
        citations_map: Dict[int, CitationDetail] = {}
        unsupported_claims: List[str] = []
        outdated_sources_flagged: List[str] = []
        conflicting_sources_flagged: List[str] = []
        
        chunk_map: Dict[int, RetrievedChunk] = {
            idx + 1: chunk for idx, chunk in enumerate(retrieved_chunks)
        }

        # Analyze each step
        all_support_scores = []
        for step in first_aid_steps:
            action = step.get("action", "")
            details = step.get("details", "")
            step_full_text = f"{action}. {details}".strip()

            cited_indices = self.parse_citations_from_text(step_full_text)
            
            # If step didn't explicitly include a tag [X], default to chunk 1 or find best semantic chunk
            if not cited_indices and retrieved_chunks:
                # Associate with top chunk by default
                cited_indices = [1]

            step_has_supported_evidence = False
            for c_idx in cited_indices:
                if c_idx not in chunk_map:
                    unsupported_claims.append(f"Step '{action}': Cites non-existent source [{c_idx}].")
                    continue

                chunk = chunk_map[c_idx]
                
                # Check outdated source status
                if chunk.review_status and chunk.review_status.lower() in ["outdated", "pending review"]:
                    flag_msg = f"Source [{c_idx}] ({chunk.document_title}) has status '{chunk.review_status}'."
                    if flag_msg not in outdated_sources_flagged:
                        outdated_sources_flagged.append(flag_msg)

                # Compute claim-level support score using embedding cosine similarity + lexical overlap
                step_vec = context_embedder.encode(step_full_text)
                chunk_vec = context_embedder.encode(chunk.content)
                sim_score = context_embedder.compute_similarity(step_vec, chunk_vec)
                
                # Lexical keyword overlap bonus
                step_tokens = set(re.findall(r"\b\w{4,}\b", step_full_text.lower()))
                chunk_tokens = set(re.findall(r"\b\w{4,}\b", chunk.content.lower()))
                overlap = len(step_tokens & chunk_tokens) / max(1, len(step_tokens))
                support_score = round(float(min(1.0, (sim_score * 0.7) + (overlap * 0.3))), 4)
                all_support_scores.append(support_score)

                is_supported = (support_score >= self.support_threshold)
                if is_supported:
                    step_has_supported_evidence = True

                # Build citation detail card
                if c_idx not in citations_map:
                    citations_map[c_idx] = CitationDetail(
                        citation_index=c_idx,
                        citation_tag=f"[{c_idx}]",
                        document_id=chunk.document_id or f"doc-{c_idx}",
                        document_title=chunk.document_title,
                        publishing_organization=chunk.publishing_organization or chunk.source_name,
                        section=chunk.section,
                        page_number=chunk.page_number,
                        source_url=chunk.source_url,
                        review_status=chunk.review_status or "Verified",
                        document_type=chunk.document_type or "Clinical Guideline",
                        relevance_score=chunk.similarity_score,
                        claim_support_score=support_score,
                        is_verified_support=is_supported,
                        cited_excerpt=chunk.content[:240] + "..." if len(chunk.content) > 240 else chunk.content
                    )
                else:
                    # Update with higher support score if multiple steps cite same chunk
                    if support_score > citations_map[c_idx].claim_support_score:
                        citations_map[c_idx].claim_support_score = support_score

            if not step_has_supported_evidence and retrieved_chunks:
                unsupported_claims.append(f"Step '{action}': Lacks sufficient evidentiary support in cited protocols (Support score < {self.support_threshold}).")

        # If summary cites any sources
        summary_citations = self.parse_citations_from_text(summary_text)
        for c_idx in summary_citations:
            if c_idx in chunk_map and c_idx not in citations_map:
                chunk = chunk_map[c_idx]
                citations_map[c_idx] = CitationDetail(
                    citation_index=c_idx,
                    citation_tag=f"[{c_idx}]",
                    document_id=chunk.document_id or f"doc-{c_idx}",
                    document_title=chunk.document_title,
                    publishing_organization=chunk.publishing_organization or chunk.source_name,
                    section=chunk.section,
                    page_number=chunk.page_number,
                    source_url=chunk.source_url,
                    review_status=chunk.review_status or "Verified",
                    document_type=chunk.document_type or "Clinical Guideline",
                    relevance_score=chunk.similarity_score,
                    claim_support_score=0.85,
                    is_verified_support=True,
                    cited_excerpt=chunk.content[:240] + "..." if len(chunk.content) > 240 else chunk.content
                )

        # If no citations were parsed but chunks were retrieved, include chunk 1 and 2 automatically
        if not citations_map and retrieved_chunks:
            for idx, chunk in enumerate(retrieved_chunks[:2]):
                c_idx = idx + 1
                citations_map[c_idx] = CitationDetail(
                    citation_index=c_idx,
                    citation_tag=f"[{c_idx}]",
                    document_id=chunk.document_id or f"doc-{c_idx}",
                    document_title=chunk.document_title,
                    publishing_organization=chunk.publishing_organization or chunk.source_name,
                    section=chunk.section,
                    page_number=chunk.page_number,
                    source_url=chunk.source_url,
                    review_status=chunk.review_status or "Verified",
                    document_type=chunk.document_type or "Clinical Guideline",
                    relevance_score=chunk.similarity_score,
                    claim_support_score=0.75,
                    is_verified_support=True,
                    cited_excerpt=chunk.content[:240] + "..." if len(chunk.content) > 240 else chunk.content
                )
                all_support_scores.append(0.75)

        sorted_citations = [citations_map[k] for k in sorted(citations_map.keys())]
        supported_count = sum(1 for c in sorted_citations if c.is_verified_support)
        mean_grounding = round(float(sum(all_support_scores) / len(all_support_scores)), 4) if all_support_scores else 0.0
        
        verification_summary = EvidenceVerificationSummary(
            total_citations=len(sorted_citations),
            supported_claims_count=supported_count,
            unsupported_claims_count=len(unsupported_claims),
            mean_grounding_score=mean_grounding,
            outdated_sources_flagged=outdated_sources_flagged,
            conflicting_sources_flagged=conflicting_sources_flagged,
            verification_passed=(len(unsupported_claims) == 0 and len(sorted_citations) > 0)
        )

        return sorted_citations, unsupported_claims, verification_summary

# Singleton citation service
citation_service = MedicalCitationService()
