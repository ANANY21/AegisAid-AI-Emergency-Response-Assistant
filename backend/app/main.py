from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .core.logging import logger
from .core.exceptions import EmergencyAppException
from .api import emergency, classification, retrieval, hospitals, history, evaluation, explainability, sources
from .services.rag_service import rag_service
from .models.classifier import TriageClassifier

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AegisAid AI Emergency Response Assistant...")
    logger.info(f"Loaded {len(rag_service.chunks)} knowledge base chunks from {settings.KNOWLEDGE_BASE_DIR}")
    logger.info(f"Groq API Key configured: {bool(settings.GROQ_API_KEY)}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Safety-Oriented, Multimodal, Retrieval-Validated Generative AI Emergency Response Assistant",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development & local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(EmergencyAppException)
async def emergency_exception_handler(request: Request, exc: EmergencyAppException):
    logger.error(f"Handled application exception on {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.message}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": True, "message": "An internal safety or processing error occurred."}
    )

# Health endpoint (must be registered before any static catch-all)
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "knowledge_base_chunks_loaded": len(rag_service.chunks),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "model": settings.GROQ_MODEL,
        "safety_guardrails_active": True
    }

# Include API Routers
app.include_router(emergency.router)
app.include_router(classification.router)
app.include_router(retrieval.router)
app.include_router(hospitals.router)
app.include_router(history.router)
app.include_router(evaluation.router)
app.include_router(explainability.router)
app.include_router(sources.router)

# Mount frontend production build if present (MUST BE AT THE END)
dist_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="static_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"})
        target_file = dist_path / full_path
        if target_file.exists() and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_path / "index.html")
