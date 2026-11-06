import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from ..config import settings
from ..schemas.sources import (
    SourceReviewStatus, MedicalDocumentType,
    MedicalSourceProvenance, SourceReviewUpdateRequest
)
from ..core.logging import logger

class MedicalSourceRegistry:
    def __init__(self, kb_dir: Path = None):
        self.kb_dir = kb_dir or settings.KNOWLEDGE_BASE_DIR
        self._sources: Dict[str, Dict[str, Any]] = {}
        self._review_log: List[Dict[str, Any]] = []
        self.reload()

    def reload(self):
        """
        Loads all medical protocols from the knowledge base directory into registry memory.
        """
        self._sources = {}
        if not self.kb_dir.exists():
            logger.warning(f"Knowledge base directory {self.kb_dir} does not exist for source registry.")
            return

        json_files = list(self.kb_dir.glob("*.json"))
        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    doc_id = doc.get("document_id") or doc.get("id", fpath.stem)
                    
                    # Freshness computation
                    last_rev = doc.get("last_reviewed_date") or doc.get("publication_date")
                    is_stale = False
                    freshness_days = None
                    if last_rev:
                        try:
                            rev_dt = datetime.strptime(last_rev, "%Y-%m-%d").date()
                            freshness_days = (date.today() - rev_dt).days
                            # Guidelines older than 1095 days (3 years) flagged as stale
                            if freshness_days > 1095:
                                is_stale = True
                        except Exception:
                            pass

                    doc_entry = {
                        "document_id": doc_id,
                        "file_path": str(fpath),
                        "file_name": fpath.name,
                        "document_title": doc.get("document_title", fpath.stem),
                        "publishing_organization": doc.get("publishing_organization") or doc.get("source_name", "Official Medical Protocol"),
                        "source_url": doc.get("source_url"),
                        "version": doc.get("version", "v1.0"),
                        "publication_date": doc.get("publication_date"),
                        "last_reviewed_date": doc.get("last_reviewed_date"),
                        "review_status": doc.get("review_status", SourceReviewStatus.VERIFIED.value),
                        "document_type": doc.get("document_type", MedicalDocumentType.CLINICAL_GUIDELINE.value),
                        "category": doc.get("category", "general"),
                        "contraindications": doc.get("contraindications", []),
                        "section_count": len(doc.get("sections", [])),
                        "sections": doc.get("sections", []),
                        "is_stale": is_stale,
                        "freshness_days": freshness_days,
                        "last_updated_at": datetime.utcnow().isoformat()
                    }
                    self._sources[doc_id] = doc_entry
            except Exception as e:
                logger.error(f"Error loading source into registry from {fpath}: {e}")

        logger.info(f"MedicalSourceRegistry loaded {len(self._sources)} trusted clinical protocols.")

    def list_sources(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists all registered sources with optional status or category filtering.
        """
        results = list(self._sources.values())
        
        if status and status.lower() != "all":
            stat_norm = status.lower().strip()
            # Map shorthand query filters
            status_map = {
                "verified": SourceReviewStatus.VERIFIED.value.lower(),
                "pending": SourceReviewStatus.PENDING_REVIEW.value.lower(),
                "pending review": SourceReviewStatus.PENDING_REVIEW.value.lower(),
                "outdated": SourceReviewStatus.OUTDATED.value.lower(),
                "unavailable": SourceReviewStatus.UNAVAILABLE.value.lower(),
                "accepted": SourceReviewStatus.VERIFIED.value.lower(),
                "rejected": SourceReviewStatus.OUTDATED.value.lower()
            }
            target_status = status_map.get(stat_norm, stat_norm)
            results = [s for s in results if s["review_status"].lower() == target_status]

        if category and category.lower() != "all":
            results = [s for s in results if s["category"].lower() == category.lower()]

        return results

    def get_source(self, document_id: str) -> Optional[Dict[str, Any]]:
        return self._sources.get(document_id)

    def update_source_review(
        self,
        document_id: str,
        update_req: SourceReviewUpdateRequest
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the clinical review status and persistence for a specific guideline.
        """
        source = self._sources.get(document_id)
        if not source:
            return None

        # Update source dict
        source["review_status"] = update_req.review_status.value
        source["last_reviewed_date"] = date.today().isoformat()
        source["last_updated_at"] = datetime.utcnow().isoformat()
        source["is_stale"] = False
        source["reviewer_notes"] = update_req.reviewer_notes
        source["reviewed_by"] = update_req.reviewed_by

        # Persist change back to underlying JSON file
        try:
            fpath = Path(source["file_path"])
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                file_data["review_status"] = update_req.review_status.value
                file_data["last_reviewed_date"] = source["last_reviewed_date"]
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(file_data, f, indent=2)
                logger.info(f"Persisted review update for {document_id} to {fpath}")
        except Exception as e:
            logger.error(f"Error persisting source review update for {document_id}: {e}")

        # Log review action
        self._review_log.append({
            "document_id": document_id,
            "document_title": source["document_title"],
            "new_status": update_req.review_status.value,
            "reviewer": update_req.reviewed_by,
            "notes": update_req.reviewer_notes,
            "timestamp": datetime.utcnow().isoformat()
        })

        return source

    def get_source_metrics(self) -> Dict[str, Any]:
        """
        Calculates verification metrics and quality indicators for dashboard review.
        """
        total = len(self._sources)
        if total == 0:
            return {
                "total_sources": 0,
                "verified_count": 0,
                "pending_review_count": 0,
                "outdated_count": 0,
                "unavailable_count": 0,
                "verification_rate_pct": 0.0,
                "total_chunks_indexed": 0,
                "stale_guidelines_count": 0
            }

        verified = sum(1 for s in self._sources.values() if s["review_status"] == SourceReviewStatus.VERIFIED.value)
        pending = sum(1 for s in self._sources.values() if s["review_status"] == SourceReviewStatus.PENDING_REVIEW.value)
        outdated = sum(1 for s in self._sources.values() if s["review_status"] == SourceReviewStatus.OUTDATED.value)
        unavailable = sum(1 for s in self._sources.values() if s["review_status"] == SourceReviewStatus.UNAVAILABLE.value)
        stale = sum(1 for s in self._sources.values() if s.get("is_stale", False))
        total_chunks = sum(s.get("section_count", 1) for s in self._sources.values())

        return {
            "total_sources": total,
            "verified_count": verified,
            "pending_review_count": pending,
            "outdated_count": outdated,
            "unavailable_count": unavailable,
            "verification_rate_pct": round((verified / total) * 100.0, 1),
            "total_chunks_indexed": total_chunks,
            "stale_guidelines_count": stale,
            "all_sources_active": (verified == total)
        }

# Singleton registry
source_registry = MedicalSourceRegistry()
