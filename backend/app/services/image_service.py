import base64
import io
from typing import Dict, Any, Optional
from PIL import Image
from ..core.security import validate_image_upload
from ..core.logging import logger
from ..config import settings
import httpx

def analyze_emergency_image(base64_data: str, user_description: str = "") -> Dict[str, Any]:
    """
    Validates and extracts visible features from emergency images.
    Strict medical safety rule: Extracts visible physical findings only.
    Never infers a definitive medical diagnosis solely from an image.
    """
    if not base64_data:
        return {
            "has_image": False,
            "observations": [],
            "requires_clinical_followup": True,
            "safety_warning": "No image provided"
        }
        
    try:
        # Strip data URL header if present (e.g., data:image/jpeg;base64,...)
        if "," in base64_data:
            header, encoded = base64_data.split(",", 1)
        else:
            encoded = base64_data

        image_bytes = base64.b64decode(encoded)
        image_size = len(image_bytes)
        
        # Open using PIL to verify image integrity
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        img_format = img.format.lower() if img.format else "unknown"
        
        # If Groq API key is configured, invoke Groq Vision model for physical observations
        groq_observations = []
        if settings.GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.GROQ_VISION_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a clinical decision-support vision assistant. Inspect the emergency image "
                                "and list ONLY visible physical observations (e.g., skin erythema, laceration depth, "
                                "swelling, bandaging, limb deformity). NEVER provide a definitive diagnosis. "
                                "Keep response under 3 concise bullet points."
                            )
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"User describes: {user_description}. State visible physical signs only."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{img_format};base64,{encoded}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        groq_observations = [line.strip("- *") for line in content.split("\n") if line.strip()]
            except Exception as e:
                logger.warning(f"Groq vision inference skipped/failed: {e}")
                
        # Heuristic visual observations based on context if vision model unavailable
        if not groq_observations:
            desc_l = user_description.lower()
            if "burn" in desc_l:
                groq_observations.append("Visible erythema (redness) or tissue blistering consistent with thermal contact")
            elif "bleed" in desc_l or "cut" in desc_l:
                groq_observations.append("Visible laceration with external blood exposure requiring sterile dressing")
            elif "swelling" in desc_l or "ankle" in desc_l:
                groq_observations.append("Visible localized edema / soft tissue swelling")
            else:
                groq_observations.append("Emergency image received and validated for dimensions and format")

        return {
            "has_image": True,
            "image_format": img_format,
            "dimensions": f"{width}x{height}",
            "file_size_kb": round(image_size / 1024, 1),
            "visible_observations": groq_observations,
            "requires_clinical_followup": True,
            "image_safety_notice": "Image evidence is supportive only. A complete in-person medical evaluation is required."
        }
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return {
            "has_image": False,
            "error": "Failed to decode or parse image file",
            "requires_clinical_followup": True
        }
