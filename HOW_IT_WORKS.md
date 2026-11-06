# AegisAid: How the Application Works & Model Architecture

A concise guide to the operational workflow and machine learning models powering **AegisAid - AI Emergency Response Assistant**.

---

## 1. How the Application Works (End-to-End Workflow)

AegisAid operates as a **strictly deterministic, zero-agentic AI pipeline** with 8 explicit processing stages:

```
[ Multimodal Input: Text / Audio / Image ]
                    │
                    ▼
[ 1. Preprocessing & Normalization ]
    - XSS sanitization, typo correction ("chokin" -> "choking"), noise removal
                    │
                    ▼
[ 2. Clinical Entity Extraction ]
    - Pydantic extraction of symptoms, body parts, age, duration, urgency indicators
                    │
                    ▼
[ 3. ML Incident Prioritization & Critical Bypass ]
    - Calibrated ML classification: LOW | MODERATE | HIGH | CRITICAL
    - If life-threatening: INSTANT CRITICAL BYPASS (Emergency 911 alert + core life saving)
                    │
                    ▼
[ 4. Medical Knowledge Retrieval (RAG) ]
    - Semantic similarity search against verified guidelines (AHA, WHO, NHS UK, Red Cross)
                    │
                    ▼
[ 5. Retrieval Relevance Validation Engine ]
    - Cosine similarity thresholding (rejection if < 0.52) & contraindication conflict checks
                    │
                    ▼
[ 6. Confidence & Safety Escalation Engine ]
    - Deterministic routing into 5 system outcomes:
      • SUFFICIENT_EVIDENCE       --> Grounded first-aid generation with citations
      • AMBIGUOUS_INPUT           --> Clarification questions (withholds advice)
      • LOW_RETRIEVAL_RELEVANCE   --> Rejects context, safely withholds advice
      • CONFLICTING_INFORMATION   --> Alerts to contradictions, directs to nurse hotline
      • CRITICAL_EMERGENCY        --> Immediate emergency dispatch & critical protocol
                    │
                    ▼
[ 7. Grounded First-Aid Response Generation ]
    - Evidence-grounded generation of step-by-step imperative first aid + visual guides
                    │
                    ▼
[ 8. Emergency Hospital & Facility Locator ]
    - Real-time GPS-based trauma facility lookup via OpenStreetMap Overpass API
```

---

## 2. Specific Models Used in AegisAid

| Model / Algorithm | Provider / Framework | Modality | Specific Role & Functionality in AegisAid | Safety & Fallback Mechanism |
|---|---|---|---|---|
| **`openai/gpt-oss-120b`** | **Groq Cloud API** (LPU Acceleration) | Text -> Text (JSON) | **Generative First-Aid Response Engine**: Receives the user narrative strictly combined with *retrieved and verified medical citations*. Formats clear, imperative first-aid steps, precautions, contraindications, and visual guide triggers. | Built-in **Deterministic Medical Protocol Engine** (AHA/WHO clinical rules) automatically executes if Groq is offline or rate-limited. |
| **`whisper-large-v3`** | **Groq Cloud Audio API** (OpenAI Whisper) | Audio -> Text | **Speech-to-Text & Clinical Translation**: Transcribes spoken emergency recordings in 90+ languages and translates them directly into clinical English for triage. | Client-side **Web Speech API** (`webkitSpeechRecognition`) handles live browser dictation; user can review and edit text before submission. |
| **`qwen/qwen3.8-27b`** | **Groq Cloud Vision API** (Alibaba Cloud) | Image + Text -> Text | **Emergency Visual Observation**: Inspects uploaded emergency images (burns, wounds, swelling, bandages) to extract objective physical observations without inferring definitive diagnoses. | Fallback **Heuristic Image Inspector** validates image dimensions, format, and extracts context-based trauma markers if vision model is unavailable. |
| **Calibrated Random Forest Classifier** (`RandomForestClassifier` + `CalibratedClassifierCV`) | **scikit-learn** (`joblib`) | Text / Structured Features -> Classification | **Incident Triage Prioritization**: Classifies incident urgency into `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`. Uses Sigmoid probability calibration to generate reliable confidence metrics for downstream escalation. | **Rule-Based Critical Override**: Life-threatening symptoms (e.g. cardiac arrest, severe respiratory failure) override ML probability to guarantee ≥96% critical recall. |
| **Dense Medical Semantic Embedding Model** | **NumPy / Custom Semantic Projection** | Text -> 128D Dense Vectors | **RAG Knowledge Base Indexing**: Projects medical guideline chunks (from AHA, WHO, NHS UK, CDC, Red Cross) and user queries into a 128-dimensional clinical semantic vector space for cosine similarity retrieval. | Strict **Retrieval Threshold Filter (0.52)** rejects off-topic queries before any medical advice can be generated. |

---

## 3. Strict Safety Guardrails (Zero-Agentic Mandate)

1. **No Autonomous Agents**: Zero self-directed planning loops, autonomous agent-to-agent chatter, or unconstrained tool calls.
2. **Retrieval Relevance Validation**: Top-retrieved documents are never assumed to be correct; they must exceed the calibrated threshold.
3. **Controlled Low-Confidence Escalation**: When information is vague or relevance is low, the system explicitly **withholds speculative advice** and requests targeted clinical clarifications.
4. **Never a Replacement for Emergency Services**: Every response emphasizes immediate local emergency contact (911 / 112 / 999 / 108).

---

## 4. Quick Execution

```bash
# Backend (Port 8000)
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

# Frontend (Port 5173)
cd frontend && npm run dev
```
