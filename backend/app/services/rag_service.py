import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from ..config import settings
from .transformer_service import context_embedder
from ..schemas.retrieval import RetrievedChunk
from ..core.logging import logger

class MedicalRAGService:
    def __init__(self, knowledge_base_dir: Path = None):
        self.kb_dir = knowledge_base_dir or settings.KNOWLEDGE_BASE_DIR
        self.documents: List[Dict[str, Any]] = []
        self.chunks: List[Dict[str, Any]] = []
        self.chunk_embeddings: Optional[np.ndarray] = None
        self.load_and_index()

    def load_and_index(self):
        """
        Ingests official medical guidelines, extracts sections into semantic chunks,
        attaches source provenance metadata, and builds dense vector embeddings.
        """
        self.documents = []
        self.chunks = []
        
        if not self.kb_dir.exists():
            logger.warning(f"Knowledge base directory {self.kb_dir} does not exist.")
            return

        json_files = list(self.kb_dir.glob("*.json"))
        logger.info(f"Loading {len(json_files)} medical protocol files from {self.kb_dir}")

        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    self.documents.append(doc)
                    
                    doc_title = doc.get("document_title", file_path.stem)
                    source_name = doc.get("source_name", "Official Medical Protocol")
                    source_url = doc.get("source_url")
                    pub_date = doc.get("publication_date")
                    contraindications = doc.get("contraindications", [])
                    category = doc.get("category", "general")
                    
                    for idx, sec in enumerate(doc.get("sections", [])):
                        sec_name = sec.get("section_name", f"Section {idx+1}")
                        content = sec.get("content", "")
                        keywords = sec.get("keywords", [])
                        visual_guide_key = sec.get("visual_guide_key")
                        
                        chunk_text = f"{doc_title} - {sec_name}. {content} Keywords: {', '.join(keywords)}"
                        
                        chunk_data = {
                            "chunk_id": f"{doc.get('id', file_path.stem)}-chunk-{idx+1}",
                            "document_title": doc_title,
                            "source_name": source_name,
                            "source_url": source_url,
                            "publication_date": pub_date,
                            "section": sec_name,
                            "content": content,
                            "keywords": keywords,
                            "contraindications": contraindications,
                            "visual_guide_key": visual_guide_key,
                            "category": category,
                            "search_text": chunk_text
                        }
                        self.chunks.append(chunk_data)
            except Exception as e:
                logger.error(f"Error parsing knowledge base file {file_path}: {e}")

        if self.chunks:
            search_texts = [c["search_text"] for c in self.chunks]
            self.chunk_embeddings = context_embedder.encode(search_texts)
            logger.info(f"Successfully indexed {len(self.chunks)} semantic medical chunks with embeddings shape {self.chunk_embeddings.shape}")
        else:
            self.chunk_embeddings = np.empty((0, context_embedder.embedding_dim))

    def retrieve(self, query: str, top_k: int = 4) -> List[RetrievedChunk]:
        """
        Retrieves top-K most relevant medical guideline chunks with source provenance and similarity scores.
        """
        if not self.chunks or self.chunk_embeddings is None or len(self.chunks) == 0:
            logger.warning("RAG retrieved called on empty knowledge base")
            return []

        query_vec = context_embedder.encode(query)
        
        # Calculate cosine similarities against all chunks
        scores = []
        for i, chunk_vec in enumerate(self.chunk_embeddings):
            sim = context_embedder.compute_similarity(query_vec, chunk_vec)
            
            # Additional lexical overlap boost for exact critical medical term matching
            q_lower = query.lower()
            keywords = self.chunks[i]["keywords"]
            kw_matches = sum(1 for kw in keywords if kw.lower() in q_lower)
            if kw_matches > 0:
                sim = min(1.0, sim + (0.08 * kw_matches))
                
            scores.append((sim, i))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        top_matches = scores[:top_k]

        results = []
        for sim, idx in top_matches:
            c = self.chunks[idx]
            results.append(RetrievedChunk(
                chunk_id=c["chunk_id"],
                document_title=c["document_title"],
                source_name=c["source_name"],
                source_url=c["source_url"],
                publication_date=c["publication_date"],
                section=c["section"],
                content=c["content"],
                similarity_score=round(float(sim), 4),
                contraindications=c["contraindications"]
            ))

        return results

# Singleton instance
rag_service = MedicalRAGService()
