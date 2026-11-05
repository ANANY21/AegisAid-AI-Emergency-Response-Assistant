from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RelevanceStatus(str, Enum):
    VALID = "VALID"
    INSUFFICIENT = "INSUFFICIENT"
    IRRELEVANT = "IRRELEVANT"
    CONFLICTING = "CONFLICTING"

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_title: str
    source_name: str = Field(..., description="WHO, NHS, American Heart Association, Red Cross, etc.")
    source_url: Optional[str] = None
    publication_date: Optional[str] = None
    section: str
    content: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    rerank_score: Optional[float] = None
    is_relevant: bool = True
    contraindications: List[str] = Field(default_factory=list)

class RetrievalValidationResult(BaseModel):
    status: RelevanceStatus
    has_sufficient_evidence: bool
    top_chunks: List[RetrievedChunk] = Field(default_factory=list)
    max_similarity: float = 0.0
    mean_similarity: float = 0.0
    threshold_applied: float
    rejection_reason: Optional[str] = None
    detected_conflicts: List[str] = Field(default_factory=list)
    provenance_verified: bool = True
