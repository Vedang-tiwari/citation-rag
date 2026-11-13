"""FastAPI main application entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown tasks."""
    # Startup
    setup_logging()
    settings.ensure_directories()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (Phase 1)...")
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Processed directory: {settings.PROCESSED_DIR}")
    yield
    # Shutdown
    logger.info("Shutting down Citation RAG...")


def create_application() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Citation-based Retrieval-Augmented Generation (RAG) System — Phase 1: Foundation & Ingestion",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register custom exception handlers
    register_exception_handlers(app)

    # Include API Routers
    app.include_router(health.router, prefix=settings.API_V1_PREFIX)
    app.include_router(health.router)  # Also expose /health at root
    app.include_router(documents.router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "phase": 1,
            "status": "online",
            "docs_url": "/docs",
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
