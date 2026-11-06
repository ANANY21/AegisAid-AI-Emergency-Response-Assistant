from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SourceReviewStatus(str, Enum):
    VERIFIED = "Verified"
    PENDING_REVIEW = "Pending Review"
    OUTDATED = "Outdated"
    UNAVAILABLE = "Unavailable"

class MedicalDocumentType(str, Enum):
    CLINICAL_GUIDELINE = "Clinical Guideline"
    EMERGENCY_PROTOCOL = "Emergency Protocol"
    FIRST_AID_MANUAL = "First Aid Manual"
    CONSENSUS_SUMMARY = "Consensus Summary"

class MedicalSourceProvenance(BaseModel):
    document_id: str
    document_title: str
    publishing_organization: str
    source_url: Optional[str] = None
    version: str = "v1.0"
    publication_date: Optional[str] = None
    last_reviewed_date: Optional[str] = None
    review_status: SourceReviewStatus = SourceReviewStatus.VERIFIED
    document_type: MedicalDocumentType = MedicalDocumentType.CLINICAL_GUIDELINE
    category: str = "general"
    contraindications: List[str] = Field(default_factory=list)
    section_count: int = 1
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    is_stale: bool = False
    freshness_days: Optional[int] = None

class SourceReviewUpdateRequest(BaseModel):
    review_status: SourceReviewStatus
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = "Clinical Board Reviewer"

class CitationDetail(BaseModel):
    citation_index: int = Field(..., description="Citation index (1-based)")
    citation_tag: str = Field(..., description="Bracketed citation tag e.g. [1]")
    document_id: str
    document_title: str
    publishing_organization: str
    section: str
    page_number: Optional[str] = None
    source_url: Optional[str] = None
    review_status: str = "Verified"
    document_type: str = "Clinical Guideline"
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    claim_support_score: float = Field(..., ge=0.0, le=1.0)
    is_verified_support: bool = True
    cited_excerpt: str

class EvidenceVerificationSummary(BaseModel):
    total_citations: int = 0
    supported_claims_count: int = 0
    unsupported_claims_count: int = 0
    mean_grounding_score: float = 0.0
    outdated_sources_flagged: List[str] = Field(default_factory=list)
    conflicting_sources_flagged: List[str] = Field(default_factory=list)
    verification_passed: bool = True
