import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .core.config import get_settings
from .core.db import create_tables
from .core.settings import AI_PROVIDER
from .services.ai_client import cache_get, cache_set

settings = get_settings()

logger = logging.getLogger("saas_app")

app = FastAPI(title=settings.app_name)
app.add_middleware(GZipMiddleware, minimum_size=1024)
allowed_origins = settings.cors_origins or ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

if settings.trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

# Global HF pipeline placeholder
HF_LOCAL_PIPELINE = None


@app.on_event("startup")
def startup_event():
    global HF_LOCAL_PIPELINE
    # create DB tables for dev
    try:
        create_tables()
    except Exception as e:
        logger.exception("Error creating tables: %s", e)

    # Initialize HF pipeline if requested
    if AI_PROVIDER == "hf_local":
        try:
            from transformers import pipeline as hf_pipeline_loader
            logger.info("Inicializando pipeline HF local en startup...")
            HF_LOCAL_PIPELINE = hf_pipeline_loader(
                "text-generation",
                model="gpt2",
                device=-1,
            )
            logger.info("HF local cargado.")
        except Exception as e:
            logger.exception("No se pudo inicializar HF local: %s", e)
            HF_LOCAL_PIPELINE = None


# Include routers
from .routers import router as api_router  # isort: skip
app.include_router(api_router)
