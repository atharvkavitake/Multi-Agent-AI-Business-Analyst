"""
Multi-Agent AI Business Analyst - FastAPI Main Application Entry Point.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import get_settings
from backend.app.database import check_database_connection, Base, engine
from backend.app.utils.logging_config import setup_logging, get_logger

settings = get_settings()
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Events (Startup & Shutdown).
    """
    logger.info("==================================================")
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[-1]}")  # safe masked log
    logger.info("==================================================")

    # Ensure required runtime directories exist
    settings.upload_dir_path
    settings.reports_dir_path

    # Initialize database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas verified/initialized successfully.")
    except Exception as e:
        logger.warning(f"Database schema initialization warning: {e}")

    # Check database connectivity
    db_ok = check_database_connection()
    if db_ok:
        logger.info("Database connection: ONLINE")
    else:
        logger.warning("Database connection: OFFLINE or UNREACHABLE")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Enterprise Multi-Agent AI Business Intelligence Platform. "
        "Provides automated exploratory data analysis, deterministic business KPIs, "
        "anomaly detection, trend analysis, strategic recommendations, natural-language "
        "dataset queries, and executive PDF report generation."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Structured handler for request body / parameter validation errors."""
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Input validation failed. Please check the submitted fields.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled server exceptions."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred while processing your request.",
        },
    )


# Core System Endpoints
@app.get("/", tags=["System"])
async def root():
    """
    Root discovery endpoint providing application metadata and documentation links.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "online",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": f"{settings.API_V1_PREFIX}/openapi.json",
        },
        "health_check": "/health",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint verifying application components,
    database connectivity, and AI service readiness.
    """
    db_healthy = check_database_connection()
    ai_configured = bool(settings.OPENROUTER_API_KEY) or settings.USE_LOCAL_OLLAMA

    overall_status = "healthy" if db_healthy else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "components": {
            "database": "online" if db_healthy else "offline",
            "ai_service": "configured" if ai_configured else "fallback_mode_only",
            "storage_upload_dir": "ready" if settings.upload_dir_path.exists() else "missing",
            "storage_reports_dir": "ready" if settings.reports_dir_path.exists() else "missing",
        },
        "ai_settings": {
            "default_model": settings.DEFAULT_LLM_MODEL,
            "fallback_model": settings.FALLBACK_LLM_MODEL,
            "local_ollama_enabled": settings.USE_LOCAL_OLLAMA,
        },
    }
