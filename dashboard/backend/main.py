"""FastAPI Application Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard.backend.api.v1 import router as api_v1_router
from bot.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Discord Management Dashboard API",
    description="Enterprise API for the Discord Management Platform.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
# In production, this should be restricted to the exact dashboard domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize resources on startup."""
    logger.info("dashboard.api.startup", status="success")
    # Initialize Redis websocket listener here in the future
    pass


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("dashboard.api.shutdown", status="success")
    pass


@app.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok", "service": "dashboard_api"}
