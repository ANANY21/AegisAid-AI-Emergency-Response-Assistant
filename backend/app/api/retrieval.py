from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from ..schemas.retrieval import RetrievedChunk, RetrievalValidationResult
from ..services.rag_service import rag_service
from ..services.retrieval_validation import retrieval_validator
from ..config import settings

router = APIRouter(prefix="/api/retrieval", tags=["RAG & Relevance Validation"])

class RetrievalSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4

@router.post("/search", response_model=List[RetrievedChunk])
def search_knowledge_base(req: RetrievalSearchRequest):
    return rag_service.retrieve(query=req.query, top_k=req.top_k or settings.RETRIEVAL_TOP_K)

@router.post("/validate", response_model=RetrievalValidationResult)
def validate_retrieval_query(req: RetrievalSearchRequest):
    chunks = rag_service.retrieve(query=req.query, top_k=req.top_k or settings.RETRIEVAL_TOP_K)
    return retrieval_validator.validate_retrieval(query=req.query, retrieved_chunks=chunks)
