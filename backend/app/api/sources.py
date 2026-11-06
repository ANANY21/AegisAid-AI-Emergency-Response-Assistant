from fastapi import APIRouter, HTTPException, Query, Path as FPath
from typing import Optional, List, Dict, Any

from ..services.source_registry import source_registry
from ..schemas.sources import (
    SourceReviewStatus, MedicalSourceProvenance,
    SourceReviewUpdateRequest
)
from ..core.logging import logger

router = APIRouter(prefix="", tags=["Medical Sources & Provenance"])

@router.get("/api/v1/sources/metrics")
@router.get("/api/sources/metrics")
def get_source_registry_metrics():
    """
    Returns aggregate medical source provenance, review statuses, and freshness metrics.
    """
    try:
        return source_registry.get_source_metrics()
    except Exception as e:
        logger.error(f"Error fetching source metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/sources")
@router.get("/api/sources")
def list_medical_sources(
    status: Optional[str] = Query(None, description="Filter by status: verified, pending, outdated, all"),
    category: Optional[str] = Query(None, description="Filter by clinical category")
):
    """
    Returns all indexed medical guideline sources with verification and provenance metadata.
    """
    try:
        stat_val = status if isinstance(status, str) else None
        cat_val = category if isinstance(category, str) else None
        return source_registry.list_sources(status=stat_val, category=cat_val)
    except Exception as e:
        logger.error(f"Error listing medical sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/sources/{document_id}")
@router.get("/api/sources/{document_id}")
def get_medical_source_by_id(
    document_id: str = FPath(..., description="Unique protocol document ID")
):
    """
    Fetches full metadata and section breakdown for a specific medical guideline document.
    """
    doc_id = document_id if isinstance(document_id, str) else str(document_id)
    source = source_registry.get_source(doc_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Medical source '{document_id}' not found.")
    return source

@router.post("/api/v1/sources/{document_id}/review")
@router.post("/api/sources/{document_id}/review")
def update_source_review_status(
    document_id: str = FPath(..., description="Unique protocol document ID"),
    payload: SourceReviewUpdateRequest = ...
):
    """
    Updates the review status and validation timestamp of a clinical protocol.
    Authorized for clinical board reviewers and administrators.
    """
    updated = source_registry.update_source_review(document_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Medical source '{document_id}' not found.")
    return {
        "status": "success",
        "message": f"Updated review status for {document_id} to {payload.review_status.value}",
        "source": updated
    }
