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
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Data Stores
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    ENV = os.getenv("ENV", "dev")
    
    # Server Configuration
    PORT = int(os.getenv("PORT", "8000"))
    NGROK_URL = os.getenv("NGROK_URL", "")
    
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
