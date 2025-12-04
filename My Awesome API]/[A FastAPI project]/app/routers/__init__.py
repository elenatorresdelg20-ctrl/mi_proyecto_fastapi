from fastapi import APIRouter

from . import upload, explain, status, forecast, metrics, report, sales

router = APIRouter()

# Health & Status
router.include_router(status.router, prefix="", tags=["status"])

# Core endpoints
router.include_router(upload.router, prefix="", tags=["upload"])
router.include_router(explain.router, prefix="", tags=["explain"])

# Advanced features
router.include_router(forecast.router, prefix="", tags=["forecast"])
router.include_router(metrics.router, prefix="", tags=["metrics"])
router.include_router(report.router, prefix="", tags=["report"])
router.include_router(sales.router, prefix="", tags=["sales"])
