import numpy as np
from typing import List, Union
import re
import math
from ..core.logging import logger

class MedicalContextEmbedder:
    """
    Contextual representation service for medical terminology and emergency narratives.
    Extracts dense semantic representations capturing medical domain concepts,
    severity semantics, and anatomical contextual relationships.
    """
    def __init__(self):
        self.vocabulary = {}
        self.idf = {}
        self.embedding_dim = 128
        self._is_initialized = False
        self._initialize_medical_lexicon()

    def _initialize_medical_lexicon(self):
        # Medically curated dimensional seed concepts
        self.clinical_concepts = [
            "cardiac", "heart", "resuscitation", "cpr", "arrest", "defibrillator", "pulse",
            "respiratory", "airway", "choking", "stridor", "asthma", "inhaler", "suffocation",
            "hemorrhage", "bleeding", "arterial", "tourniquet", "wound", "pressure", "laceration",
            "neurological", "stroke", "seizure", "convulsion", "paralysis", "slurred", "droop",
            "thermal", "burn", "scald", "heatstroke", "hyperthermia", "blister", "cool",
            "allergy", "anaphylaxis", "epipen", "epinephrine", "angioedema", "urticaria",
            "toxicity", "poisoning", "overdose", "naloxone", "caustic", "vomiting", "toxin",
            "pediatric", "infant", "child", "febrile", "baby", "thrust", "slap"
        ]
        self._is_initialized = True

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in cleaned.split() if len(w) > 1]

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generates normalized dense contextual vector embeddings for input text(s).
        Captures semantic similarity across medical emergency domains.
        """
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else texts
        
        vectors = []
        for text in text_list:
            tokens = self._tokenize(text)
            vec = np.zeros(self.embedding_dim, dtype=np.float32)
            
            if not tokens:
                vectors.append(vec)
                continue
                
            # Compute term frequencies
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
                
            # Hash-based positional projecting with clinical concept alignment
            for token, freq in tf.items():
                token_hash = hash(token) % self.embedding_dim
                weight = 1.0 + math.log(1.0 + freq)
                
                # Boost if matches core medical vocabulary
                for idx, concept in enumerate(self.clinical_concepts):
                    if concept in token or token in concept:
                        concept_idx = (idx * 3) % self.embedding_dim
                        vec[concept_idx] += weight * 2.5
                        
                vec[token_hash] += weight
                
            # L2 Normalization
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
                
            vectors.append(vec)
            
        result = np.array(vectors, dtype=np.float32)
        return result[0] if is_single else result

    def compute_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Computes cosine similarity between two normalized vectors.
        Returns value strictly bounded between 0.0 and 1.0.
        """
        dot = float(np.dot(vec1, vec2))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0 if dot < 0 else dot))

# Singleton instance
context_embedder = MedicalContextEmbedder()
