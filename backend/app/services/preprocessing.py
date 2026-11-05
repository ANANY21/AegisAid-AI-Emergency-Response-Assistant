import re
import unicodedata
from typing import Dict, Any, List, Optional
from ..core.security import sanitize_text_input
from ..core.logging import logger

# Medical spelling corrections commonly mistyped during high-stress emergencies
COMMON_TYPOS = {
    "choking": ["chokin", "chokking", "chokng", "chokingg"],
    "breathing": ["breathin", "breathng", "breathingg", "breating"],
    "unconscious": ["unconcious", "unconciouss", "unconshus", "unconciousness"],
    "bleeding": ["bleding", "bleading", "bleedng"],
    "seizure": ["siezure", "sezure", "seisure"],
    "allergic": ["alergic", "allergik"],
    "anaphylaxis": ["anafilaxis", "anaphylactic", "anaphlaxis"],
    "stroke": ["strok", "storke"],
    "inhaler": ["inhailer", "inhealer"],
    "ambulance": ["ambulense", "ambulanc", "ambulence"]
}

def clean_and_normalize_text(raw_text: str) -> Dict[str, Any]:
    """
    Cleans, normalizes, detects typos, and sanitizes emergency text.
    Preserves all medically relevant terms and punctuation.
    """
    if not raw_text:
        return {
            "cleaned_text": "",
            "tokens": [],
            "language": "en",
            "has_injection_risk": False,
            "corrected_typos": []
        }
        
    sanitized, has_injection = sanitize_text_input(raw_text)
    
    # Unicode NFKD normalization
    normalized = unicodedata.normalize("NFKD", sanitized)
    
    # Normalize multiple whitespace, tabs, and newlines
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    
    # Typo correction for high-stress emergency keywords
    words = normalized.split()
    corrected_words = []
    corrections_made = []
    
    for word in words:
        clean_w = re.sub(r"[^\w]", "", word).lower()
        corrected = word
        for target, typos in COMMON_TYPOS.items():
            if clean_w in typos:
                corrected = word.lower().replace(clean_w, target)
                corrections_made.append(f"{clean_w} -> {target}")
                break
        corrected_words.append(corrected)
        
    final_text = " ".join(corrected_words)
    tokens = re.findall(r"\b\w+\b", final_text.lower())
    
    # Basic language detection (Latin / English default)
    is_mostly_ascii = all(ord(c) < 128 for c in final_text if c.isalpha())
    language = "en" if is_mostly_ascii else "multilingual_detected"
    
    return {
        "cleaned_text": final_text,
        "tokens": tokens,
        "language": language,
        "has_injection_risk": has_injection,
        "corrected_typos": corrections_made
    }
