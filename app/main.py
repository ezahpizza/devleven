"""
FastAPI implementation of Twilio-ElevenLabs voice calling assistant.

"""
import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from config import Config
from db import init_mongo, close_mongo
from routes import register_outbound_routes, register_webhook_routes, register_dashboard_routes


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for troubleshooting
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Silence noisy third-party loggers
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.INFO)
logging.getLogger("handlers.websocket_handler").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup."""
    try:
        await init_mongo()
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

# Enable CORS for the dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return JSONResponse(content={
        "message": "Server is running",
        "version": "2.0.0",
        "service": "DevFuzzion ElevenLabs-Twilio Integration"
    })


@app.get("/static/brochure.pdf")
async def get_brochure():
    """Serve the brochure PDF file for WhatsApp media messages."""
    # Resolve the brochure path relative to the app directory
    app_dir = Path(__file__).parent
    brochure_path = app_dir.parent / Config.BROCHURE_FILE_PATH
    
    if not brochure_path.exists():
        logger.error(f"[Static] Brochure file not found at: {brochure_path}")
        return JSONResponse(
            status_code=404,
            content={"error": "Brochure file not found"}
        )
    
    return FileResponse(
        path=str(brochure_path),
        media_type="application/pdf",
        filename="DevFuzzion_Brochure.pdf"
    )


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (REMOVE IN PRODUCTION)."""
    return JSONResponse(content={
        "webhook_secret_configured": bool(Config.ELEVENLABS_WEBHOOK_SECRET),
        "webhook_secret_length": len(Config.ELEVENLABS_WEBHOOK_SECRET) if Config.ELEVENLABS_WEBHOOK_SECRET else 0,
        "webhook_secret_preview": Config.ELEVENLABS_WEBHOOK_SECRET[:8] + "..." if Config.ELEVENLABS_WEBHOOK_SECRET else "Not set"
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
