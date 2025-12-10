"""Service for WhatsApp messaging via Twilio Programmable Messaging."""
import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin

from twilio.rest import Client as TwilioClient

from config import Config

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending WhatsApp messages using Twilio."""
    
    _client: Optional[TwilioClient] = None
    
    @classmethod
    def _get_client(cls) -> TwilioClient:
        """Get or create the Twilio client."""
        if cls._client is None:
            Config.validate_twilio_config()
            cls._client = TwilioClient(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        return cls._client
    
    @classmethod
    async def send_call_summary_whatsapp(
        cls,
        to_number: str,
        client_name: str,
        summary: str,
        follow_up_date: Optional[str] = None,
        call_id: Optional[str] = None
    ) -> dict:
        """
        Send a call summary via WhatsApp with interactive buttons.
        
        Args:
            to_number: Recipient phone number in E.164 format (e.g., +1234567890).
            client_name: Name of the client.
            summary: AI-generated call summary.
            follow_up_date: Follow-up date in YYYY-MM-DD format (optional).
            call_id: Call ID for callback reference (optional).
            
        Returns:
            dict: Response containing message SID and status.
            
        Raises:
            Exception: If message sending fails.
        """
        try:
            client = cls._get_client()
            
            # Format the WhatsApp number
            whatsapp_to = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
            whatsapp_from = f"whatsapp:{Config.TWILIO_WHATSAPP_NUMBER}"
            
            # Build the message content
            follow_up_text = f"\n\n📅 *Scheduled Follow-up:* {follow_up_date}" if follow_up_date else ""
            
            message_body = f"""📞 *Call Summary for {client_name}*

Hello {client_name}! Thank you for your recent call. Here's a summary of our conversation:

📝 *Summary:*
{summary}{follow_up_text}

---
_This is an automated message from DevFuzzion Voice Assistant._"""

            # Send the message using Twilio's WhatsApp API
            message = await asyncio.to_thread(
                client.messages.create,
                from_=whatsapp_from,
                to=whatsapp_to,
                body=message_body
            )
            
            logger.info(f"[WhatsApp] Message sent successfully to {to_number}, sid: {message.sid}")
            
            # If follow-up date exists, send interactive message with buttons
            if follow_up_date and call_id:
                await cls._send_interactive_buttons(
                    client, whatsapp_from, whatsapp_to, follow_up_date, call_id
                )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "to": to_number,
                "status": message.status
            }
            
        except Exception as e:
            logger.error(f"[WhatsApp] Failed to send message to {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_number
            }
    
    @classmethod
    async def _send_interactive_buttons(
        cls,
        client: TwilioClient,
        from_number: str,
        to_number: str,
        follow_up_date: str,
        call_id: str
    ) -> None:
        """
        Send interactive message with Confirm and Reschedule buttons.
        
        Note: This uses Twilio's Content API for interactive templates.
        For production, you should set up a WhatsApp Business approved template.
        """
        try:
            # Build callback URL for button responses
            base_url = Config.NGROK_URL or f"http://localhost:{Config.PORT}"
            callback_url = urljoin(base_url, "/webhook/whatsapp_response")
            
            # Send a follow-up message prompting action
            action_message = f"""Would you like to confirm or reschedule your follow-up appointment on {follow_up_date}?

Reply with:
✅ *CONFIRM* - to confirm the appointment
📅 *RESCHEDULE* - to request a different time

Reference: {call_id}"""
            
            message = await asyncio.to_thread(
                client.messages.create,
                from_=from_number,
                to=to_number,
                body=action_message
            )
            
            logger.info(f"[WhatsApp] Interactive prompt sent, sid: {message.sid}")
            
        except Exception as e:
            logger.warning(f"[WhatsApp] Failed to send interactive buttons: {e}")
    
    @classmethod
    async def send_simple_message(
        cls,
        to_number: str,
        message_body: str
    ) -> dict:
        """
        Send a simple WhatsApp message.
        
        Args:
            to_number: Recipient phone number in E.164 format.
            message_body: Message content.
            
        Returns:
            dict: Response containing message SID and status.
        """
        try:
            client = cls._get_client()
            
            whatsapp_to = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
            whatsapp_from = f"whatsapp:{Config.TWILIO_WHATSAPP_NUMBER}"
            
            message = await asyncio.to_thread(
                client.messages.create,
                from_=whatsapp_from,
                to=whatsapp_to,
                body=message_body
            )
            
            logger.info(f"[WhatsApp] Simple message sent to {to_number}, sid: {message.sid}")
            
            return {
                "success": True,
                "message_sid": message.sid,
                "to": to_number,
                "status": message.status
            }
            
        except Exception as e:
            logger.error(f"[WhatsApp] Failed to send simple message to {to_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "to": to_number
            }
