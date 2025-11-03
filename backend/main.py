# backend/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import generate
from app.core.config import settings
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Website Factory API",
    description="Generate complete websites using AI agents",
    version="1.0.0"
)

# Validate configuration on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Website Factory API...")

    # Validate AI provider configuration
    provider = settings.AI_PROVIDER.lower()
    if provider not in ["openai", "anthropic"]:
        logger.error(f"Invalid AI_PROVIDER: {provider}. Must be 'openai' or 'anthropic'.")
        raise ValueError(f"Invalid AI_PROVIDER: {provider}")

    # Validate API keys
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY is not set but AI_PROVIDER is 'openai'")
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        logger.info(f"✓ Using OpenAI with model: {settings.AI_MODEL}")
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY is not set but AI_PROVIDER is 'anthropic'")
            raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")
        logger.info(f"✓ Using Anthropic with model: {settings.AI_MODEL}")

    logger.info(f"✓ AI Temperature: {settings.AI_TEMPERATURE}")
    logger.info(f"✓ Max Tokens: {settings.AI_MAX_TOKENS}")
    logger.info("✓ API startup validation complete")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please check the server logs.",
            "detail": str(exc)
        },
    )

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(generate.router, prefix="/api")

# Health check endpoint
@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "AI Website Factory API",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """Detailed health check endpoint"""
    provider = settings.AI_PROVIDER.lower()
    has_key = False

    if provider == "openai":
        has_key = bool(settings.OPENAI_API_KEY)
    elif provider == "anthropic":
        has_key = bool(settings.ANTHROPIC_API_KEY)

    return {
        "status": "healthy",
        "ai_provider": provider,
        "ai_model": settings.AI_MODEL,
        "api_key_configured": has_key,
        "temperature": settings.AI_TEMPERATURE,
        "max_tokens": settings.AI_MAX_TOKENS
    }