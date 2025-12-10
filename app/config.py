"""Configuration management for the application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
    ELEVENLABS_WEBHOOK_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET", "")
    
    # Google Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", os.getenv("TWILIO_PHONE_NUMBER"))
    
    # Gmail SMTP Email Configuration
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    GMAIL_FROM_EMAIL = os.getenv("GMAIL_FROM_EMAIL", os.getenv("GMAIL_USER", ""))
    
    # Data Stores
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    ENV = os.getenv("ENV", "dev")
    
    # Server Configuration
    PORT = int(os.getenv("PORT", "8000"))
    NGROK_URL = os.getenv("NGROK_URL", "")

    # CORS Configuration (origins only)
    _cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
    if _cors_origins.strip():
        CORS_ALLOW_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
    else:
        CORS_ALLOW_ORIGINS = ["*"]
    
    @classmethod
    def validate_elevenlabs_config(cls):
        """Validate ElevenLabs configuration."""
        if not cls.ELEVENLABS_API_KEY or not cls.ELEVENLABS_AGENT_ID:
            raise ValueError("Missing ELEVENLABS_API_KEY or ELEVENLABS_AGENT_ID")
    
    @classmethod
    def validate_twilio_config(cls):
        """Validate Twilio configuration."""
        if not all([cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_PHONE_NUMBER]):
            raise ValueError("Missing Twilio configuration variables")
    
    @classmethod
    def validate_mongo_config(cls):
        """Validate MongoDB configuration."""
        if not cls.MONGO_URI:
            raise ValueError("Missing MONGO_URI")
    
    @classmethod
    def validate_email_config(cls):
        """Validate Gmail SMTP email configuration."""
        if not cls.GMAIL_USER or not cls.GMAIL_APP_PASSWORD:
            raise ValueError("Missing GMAIL_USER or GMAIL_APP_PASSWORD")
    
    @classmethod
    def validate_whatsapp_config(cls):
        """Validate WhatsApp configuration."""
        cls.validate_twilio_config()
        if not cls.TWILIO_WHATSAPP_NUMBER:
            raise ValueError("Missing TWILIO_WHATSAPP_NUMBER")
