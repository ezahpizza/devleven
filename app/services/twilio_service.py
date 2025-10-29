"""Service for Twilio API interactions."""
import asyncio
import logging

from twilio.rest import Client as TwilioClient

from config import Config

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for Twilio API operations."""
    
    def __init__(self):
        """Initialize Twilio client."""
        Config.validate_twilio_config()
        self.client = TwilioClient(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    
    async def initiate_call(self, to_number: str, twiml_url: str) -> dict:
        """
        Initiate an outbound call using Twilio.
        
        Args:
            to_number: Phone number to call
            twiml_url: URL for TwiML instructions
            
        Returns:
            dict: Call information including call SID
            
        Raises:
            Exception: If the call fails to initiate
        """
        try:
            call = await asyncio.to_thread(
                self.client.calls.create,
                from_=Config.TWILIO_PHONE_NUMBER,
                to=to_number,
                url=twiml_url,
            )
            
            logger.info(f"[Twilio] Call initiated: {call.sid} to {to_number}")
            
            return {
                "call_sid": call.sid,
                "to": to_number,
                "from": Config.TWILIO_PHONE_NUMBER,
                "status": call.status
            }
        
        except Exception as e:
            logger.error(f"[Twilio] Error initiating call: {e}")
            raise
    
    async def end_call(self, call_sid: str) -> dict:
        """
        End an active call using Twilio.
        
        Args:
            call_sid: The SID of the call to end
            
        Returns:
            dict: Call information after ending
            
        Raises:
            Exception: If the call fails to end
        """
        try:
            call = await asyncio.to_thread(
                self.client.calls(call_sid).update,
                status="completed",
            )
            
            logger.info(f"[Twilio] Call ended: {call_sid}")
            
            return {
                "call_sid": call.sid,
                "status": call.status
            }
        
        except Exception as e:
            logger.error(f"[Twilio] Error ending call {call_sid}: {e}")
            raise
