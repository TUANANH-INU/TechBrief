"""Main FastAPI application"""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import settings
from src.models.database import init_db
from src.schedulers.daily_research import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(level=settings.log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan management for FastAPI app"""
    # Startup
    logger.info("🚀 Starting TechBrief Research System...")
    init_db()
    start_scheduler()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    stop_scheduler()
    logger.info("Application stopped")


# Create FastAPI app
app = FastAPI(
    title="TechBrief Research System",
    description="AI-powered daily tech news research and synthesis",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TechBrief Research System",
        "version": "1.0.0",
        "description": "AI-powered daily tech news research and synthesis",
        "docs": "/docs",
        "health": "/api/research/health",
    }


@app.get("/status")
async def status():
    """Application status"""
    return {
        "status": "running",
        "scheduler_enabled": settings.scheduler_enabled,
        "ollama_url": settings.ollama_base_url,
        "database_configured": bool(settings.database_url),
    }


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=settings.log_level.lower())
