import re
import html
from typing import Tuple

# Common prompt injection signatures to detect and neutralize
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"system\s*prompt",
    r"act\s+as\s+an\s+unrestricted",
    r"disregard\s+all\s+rules",
    r"override\s+safety\s+protocols",
    r"delete\s+all\s+guidance",
    r"<script.*?>",
    r"javascript:"
]

def sanitize_text_input(raw_text: str) -> Tuple[str, bool]:
    """
    Sanitizes user input by stripping malicious HTML/scripts,
    escaping characters, and detecting prompt injection attempts.
    Returns: (sanitized_text, contains_injection_flag)
    """
    if not raw_text:
        return "", False
        
    text = raw_text.strip()
    
    # Check for prompt injection markers
    has_injection = False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            has_injection = True
            break
            
    # Escape HTML to prevent XSS
    escaped_text = html.escape(text)
    
    # Remove control characters except standard line breaks
    cleaned_text = "".join(ch for ch in escaped_text if ch == "\n" or ch == "\t" or 32 <= ord(ch) <= 126 or ord(ch) > 127)
    
    return cleaned_text, has_injection

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_image_upload(content_type: str, file_size: int) -> bool:
    if content_type not in ALLOWED_IMAGE_TYPES:
        return False
    if file_size > MAX_IMAGE_SIZE_BYTES:
        return False
    return True
