"""
FastAPI implementation of Twilio-ElevenLabs voice calling assistant.

"""
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import Config
from db import init_mongo, close_mongo
from routes import register_outbound_routes, register_webhook_routes, register_dashboard_routes


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup."""
    logger.info("[Server] Starting application...")
    
    try:
        await init_mongo()
        logger.info("[Server] MongoDB initialized")
    except Exception as e:
        logger.error(f"[Server] MongoDB initialization failed: {e}")
    
    try:
        yield
    finally:
        await close_mongo()


# Initialize FastAPI application
app = FastAPI(
    title="Twilio-ElevenLabs Voice Assistant",
    description="Connect Twilio phone calls to ElevenLabs Conversational AI",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return JSONResponse(content={
        "message": "Server is running",
        "version": "2.0.0",
        "service": "DevFusion ElevenLabs-Twilio Integration"
    })


# Register route handlers
register_outbound_routes(app)
register_dashboard_routes(app)
register_webhook_routes(app)


if __name__ == "__main__":
    logger.info(f"[Server] Starting on port {Config.PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=False,
        log_level="info"
    )
