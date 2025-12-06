import asyncio
import logging
import time

from fastapi import FastAPI, Request

from .core.db import create_tables
from .core.settings import AI_PROVIDER
from .services.ai_client import cache_get, cache_set

logger = logging.getLogger("saas_app")

app = FastAPI(title="SaaS Reporting AI - Modular")

# Global HF pipeline placeholder
HF_LOCAL_PIPELINE = None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    tenant_code = getattr(request.state, "tenant_code", None) or (request.scope.get("path_params") or {}).get("tenant_code")
    logger.info(
        "HTTP %s %s tenant=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        tenant_code or "-",
        response.status_code,
        duration_ms,
    )
    return response


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
