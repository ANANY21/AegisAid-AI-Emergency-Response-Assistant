import re
import io
from typing import Dict, Any, Optional
import httpx
from .preprocessing import clean_and_normalize_text
from ..config import settings
from ..core.logging import logger

def process_voice_transcription(raw_transcription: str) -> Dict[str, Any]:
    """
    Cleans up speech-to-text artifacts, removes verbal hesitations ('um', 'uh', 'ah'),
    normalizes medical punctuation, and performs translation if foreign language detected.
    """
    if not raw_transcription:
        return {
            "processed_text": "",
            "hesitation_count": 0,
            "was_modified": False,
            "detected_language": "en"
        }
        
    text = raw_transcription.strip()
    
    # Remove filler speech sounds
    hesitation_patterns = r"\b(um|uh|uhh|umm|ah|er|like,?\s+you\s+know)\b"
    hesitations = re.findall(hesitation_patterns, text, flags=re.IGNORECASE)
    cleaned_speech = re.sub(hesitation_patterns, "", text, flags=re.IGNORECASE)
    
    # Normalize spacing
    cleaned_speech = re.sub(r"\s+", " ", cleaned_speech).strip()
    
    # Capitalize first letter of sentences
    cleaned_speech = ". ".join(s.strip().capitalize() for s in cleaned_speech.split(".") if s.strip())
    
    preprocess_result = clean_and_normalize_text(cleaned_speech)
    cleaned_text = preprocess_result["cleaned_text"]

    # If foreign language is detected or text contains non-ASCII characters,
    # invoke translation into English to ensure safe triage
    translated_text = cleaned_text
    detected_lang = preprocess_result.get("language", "en")
    
    if settings.GROQ_API_KEY and (detected_lang != "en" or any(ord(c) > 127 for c in cleaned_text)):
        try:
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a clinical emergency translator. Translate the patient's statement directly into English. Preserve all medical symptoms, body parts, duration, and urgency. Return ONLY the English translation without preamble."
                    },
                    {
                        "role": "user",
                        "content": cleaned_text
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 200
            }
            with httpx.Client(timeout=8.0) as client:
                resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    translated_text = resp.json()["choices"][0]["message"]["content"].strip()
                    logger.info(f"Translated foreign speech: '{cleaned_text}' -> '{translated_text}'")
        except Exception as e:
            logger.warning(f"Speech translation via Groq failed: {e}")

    return {
        "processed_text": translated_text,
        "original_text": cleaned_text,
        "hesitation_count": len(hesitations),
        "was_modified": len(hesitations) > 0 or len(preprocess_result["corrected_typos"]) > 0 or translated_text != cleaned_text,
        "corrections": preprocess_result["corrected_typos"],
        "detected_language": detected_lang
    }

def transcribe_and_translate_audio_file(
    file_bytes: bytes,
    filename: str = "emergency_audio.webm",
    translate_to_english: bool = True
) -> Dict[str, Any]:
    """
    Transcribes and translates recorded audio file using Groq Whisper API (whisper-large-v3).
    Supports all major world languages and automatically translates emergency speech into English.
    """
    if not file_bytes or len(file_bytes) == 0:
        return {
            "success": False,
            "transcription": "",
            "error": "Empty audio recording received"
        }

    if settings.GROQ_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}"
            }
            
            # Select Groq Whisper endpoint: translations (into English) or transcriptions
            endpoint = (
                "https://api.groq.com/openai/v1/audio/translations"
                if translate_to_english
                else "https://api.groq.com/openai/v1/audio/transcriptions"
            )
            
            files = {
                "file": (filename, file_bytes, "audio/webm")
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "json"
            }
            
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(endpoint, headers=headers, files=files, data=data)
                if resp.status_code == 200:
                    raw_text = resp.json().get("text", "")
                    processed = process_voice_transcription(raw_text)
                    return {
                        "success": True,
                        "transcription": processed["processed_text"],
                        "original_transcription": raw_text,
                        "provider": "Groq Whisper (whisper-large-v3)",
                        "translated": translate_to_english
                    }
                else:
                    logger.warning(f"Groq Whisper returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Groq Whisper audio transcription failed: {e}")

    # Fallback response if Groq API key is not configured or fails
    return {
        "success": False,
        "transcription": "",
        "error": "Groq API key not configured for server-side audio transcription. In-browser speech recognition is active."
    }
