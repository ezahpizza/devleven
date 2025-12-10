"""Webhook handlers for voice agent call completion."""
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Header, Form
from fastapi.responses import JSONResponse, Response

from config import Config
from handlers.dashboard_ws import dashboard_manager
from models import (
    CallCompletePayload, 
    CallRecordResponse, 
    ElevenLabsWebhookPayload,
    InsightModel,
    NotificationPreferences
)
from services.call_record_service import CallRecordService
from services.gemini_service import GeminiService
from services.email_service import EmailService
from services.whatsapp_service import WhatsAppService
from utils.webhook_security import verify_hmac_signature

logger = logging.getLogger(__name__)


def register_webhook_routes(app):
    """Register webhook routes."""
    router = APIRouter(tags=["Webhooks"])

    @router.post("/webhook/call_complete")
    async def call_complete_webhook(
        request: Request,
        elevenlabs_signature: str = Header(None, alias="ElevenLabs-Signature")
    ):
        """
        Persist call completion payloads and trigger dashboard updates.
        
        This endpoint verifies the HMAC signature from ElevenLabs before processing.
        """
        try:
            # Get raw request body for signature verification
            raw_body = await request.body()
            
            # Verify HMAC signature if webhook secret is configured
            if Config.ELEVENLABS_WEBHOOK_SECRET:
                if not elevenlabs_signature:
                    raise HTTPException(
                        status_code=401,
                        detail="Missing ElevenLabs-Signature header"
                    )
                
                if not verify_hmac_signature(
                    raw_body,
                    elevenlabs_signature,
                    Config.ELEVENLABS_WEBHOOK_SECRET
                ):
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid webhook signature"
                    )
            
            # Parse and validate payload
            try:
                raw_data = json.loads(raw_body)
                
                # Parse as ElevenLabs webhook format
                elevenlabs_payload = ElevenLabsWebhookPayload.model_validate(raw_data)
                
                # Transform ElevenLabs payload to our internal format
                # Build transcript text from conversation turns
                transcript_text = ""
                for turn in elevenlabs_payload.data.transcript:
                    if turn.message:
                        role_label = turn.role.capitalize()
                        transcript_text += f"{role_label}: {turn.message}\n"
                
                # Extract client name from stored metadata (set during call initiation)
                conversation_id = elevenlabs_payload.data.conversation_id
                metadata = await CallRecordService.get_call_metadata_by_conversation(conversation_id)
                
                client_name = metadata.get("client_name", "Unknown")
                if client_name != "Unknown":
                    logger.info(f"[Webhook] Using stored client name: {client_name}")
                else:
                    logger.warning(f"[Webhook] No stored metadata found for conversation_id={conversation_id}")
                    
                    # Fallback: Try to get from webhook payload (legacy support)
                    if 'conversation_initiation_client_data' in raw_data.get('data', {}):
                        init_data = raw_data['data']['conversation_initiation_client_data']
                        if isinstance(init_data, dict):
                            dynamic_vars = init_data.get('dynamic_variables', {})
                            if isinstance(dynamic_vars, dict):
                                client_name = dynamic_vars.get('client_name', 'Unknown')
                                logger.info(f"[Webhook] Fallback: Extracted client name from payload: {client_name}")
                
                # Extract topics from summary if available
                topics = []
                if elevenlabs_payload.data.analysis and elevenlabs_payload.data.analysis.call_summary_title:
                    topics = [elevenlabs_payload.data.analysis.call_summary_title]
                
                # Determine conversion status (you may want to adjust this logic)
                conversion_status = (
                    elevenlabs_payload.data.analysis.call_successful == "success"
                    if elevenlabs_payload.data.analysis else False
                )
                
                # Create our internal payload format
                payload = CallCompletePayload(
                    call_id=elevenlabs_payload.data.conversation_id,
                    client_name=client_name,
                    transcript=transcript_text.strip(),
                    insights=InsightModel(
                        topics=topics,
                        duration_sec=elevenlabs_payload.data.metadata.call_duration_secs
                    ),
                    conversion_status=conversion_status,
                    timestamp=datetime.fromtimestamp(elevenlabs_payload.event_timestamp, tz=timezone.utc)
                )
                
                # Get the phone number from metadata
                phone_number = metadata.get("phone_number", "")
                
                # Generate AI summary, extract follow-up date and notification preferences using Gemini
                try:
                    analysis_result = await GeminiService.analyze_transcript(
                        transcript_text.strip(),
                        default_phone_number=phone_number
                    )
                    payload.summary = analysis_result.summary
                    payload.follow_up_date = analysis_result.follow_up_date
                    payload.phone_number = phone_number
                    
                    # Set notification preferences
                    payload.notification_preferences = NotificationPreferences(
                        notify_email=analysis_result.notify_email,
                        notify_whatsapp=analysis_result.notify_whatsapp,
                        email_address=analysis_result.email_address,
                        whatsapp_number=analysis_result.whatsapp_number
                    )
                    
                    logger.info(f"[Webhook] Gemini analysis complete - summary: {analysis_result.summary[:50]}..., "
                               f"follow_up: {analysis_result.follow_up_date}, "
                               f"notify_email: {analysis_result.notify_email}, "
                               f"notify_whatsapp: {analysis_result.notify_whatsapp}")
                except Exception as gemini_error:
                    logger.warning(f"[Webhook] Gemini analysis failed, continuing without summary: {gemini_error}")
                    payload.summary = None
                    payload.follow_up_date = None
                    payload.notification_preferences = None
                
            except Exception as e:
                logger.error(f"[Webhook] Failed to parse payload: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")
            
            # Process the webhook
            record = await CallRecordService.upsert_call_record(payload)
            response_model = CallRecordResponse(**record)
            
            # Send post-call notifications
            await _send_post_call_notifications(payload, record)
            
            # Clean up stored metadata
            await CallRecordService.cleanup_call_metadata(conversation_id)
            
            # Broadcast full record so the dashboard stays in sync
            await dashboard_manager.broadcast(
                "call_completed",
                response_model.model_dump(mode="json"),
            )
            
            return {"status": "success", "call_id": response_model.call_id}
            
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - network/db errors
            logger.error("[Webhook] call_complete error: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to process webhook")

    @router.post("/webhook/whatsapp_response")
    async def whatsapp_response_webhook(
        request: Request,
        Body: str = Form(default=""),
        From: str = Form(default=""),
        To: str = Form(default="")
    ):
        """
        Handle incoming WhatsApp message responses (confirm/reschedule).
        
        This endpoint receives webhooks from Twilio when users reply to WhatsApp messages.
        """
        try:
            # Parse the incoming message
            message_body = Body.strip().upper()
            from_number = From.replace("whatsapp:", "")
            
            logger.info(f"[WhatsApp Webhook] Received response from {from_number}: {message_body}")
            
            # Handle user responses
            if message_body == "CONFIRM":
                # User confirmed the appointment
                response_message = "✅ Great! Your appointment has been confirmed. We look forward to speaking with you!"
                await WhatsAppService.send_simple_message(from_number, response_message)
                
                # TODO: Update the call record with confirmation status
                logger.info(f"[WhatsApp Webhook] Appointment confirmed by {from_number}")
                
            elif message_body == "RESCHEDULE":
                # User wants to reschedule
                response_message = "📅 No problem! Please call us back at your convenience to reschedule your appointment, or reply with your preferred date and time."
                await WhatsAppService.send_simple_message(from_number, response_message)
                
                logger.info(f"[WhatsApp Webhook] Reschedule requested by {from_number}")
            
            else:
                # Generic response for other messages
                response_message = "Thank you for your message. If you'd like to confirm your appointment, reply CONFIRM. To reschedule, reply RESCHEDULE."
                await WhatsAppService.send_simple_message(from_number, response_message)
            
            # Return empty TwiML response
            return Response(content="", media_type="application/xml")
            
        except Exception as exc:
            logger.error(f"[WhatsApp Webhook] Error processing response: {exc}")
            return Response(content="", media_type="application/xml")

    app.include_router(router)


async def _send_post_call_notifications(payload: CallCompletePayload, record: dict) -> None:
    """
    Send post-call notifications via email and/or WhatsApp based on user preferences.
    
    Args:
        payload: The call completion payload with notification preferences.
        record: The saved call record.
    """
    if not payload.notification_preferences:
        logger.info("[PostCallNotifications] No notification preferences set, skipping")
        return
    
    prefs = payload.notification_preferences
    
    # Send email notification if requested
    if prefs.notify_email and prefs.email_address:
        try:
            email_result = await EmailService.send_call_summary_email(
                to_email=prefs.email_address,
                client_name=payload.client_name,
                summary=payload.summary or "No summary available.",
                follow_up_date=payload.follow_up_date
            )
            
            if email_result.get("success"):
                logger.info(f"[PostCallNotifications] Email sent to {prefs.email_address}")
                # Update the record to mark email as sent
                prefs.email_sent = True
            else:
                logger.warning(f"[PostCallNotifications] Email failed: {email_result.get('error')}")
        except Exception as e:
            logger.error(f"[PostCallNotifications] Email error: {e}")
    
    # Send WhatsApp notification if requested
    if prefs.notify_whatsapp and prefs.whatsapp_number:
        try:
            whatsapp_result = await WhatsAppService.send_call_summary_whatsapp(
                to_number=prefs.whatsapp_number,
                client_name=payload.client_name,
                summary=payload.summary or "No summary available.",
                follow_up_date=payload.follow_up_date,
                call_id=payload.call_id
            )
            
            if whatsapp_result.get("success"):
                logger.info(f"[PostCallNotifications] WhatsApp sent to {prefs.whatsapp_number}")
                # Update the record to mark WhatsApp as sent
                prefs.whatsapp_sent = True
            else:
                logger.warning(f"[PostCallNotifications] WhatsApp failed: {whatsapp_result.get('error')}")
        except Exception as e:
            logger.error(f"[PostCallNotifications] WhatsApp error: {e}")
    
    # Update record with notification status if any were sent
    if prefs.email_sent or prefs.whatsapp_sent:
        try:
            updated_payload = CallCompletePayload(**record)
            updated_payload.notification_preferences = prefs
            await CallRecordService.upsert_call_record(updated_payload)
            logger.info("[PostCallNotifications] Updated record with notification status")
        except Exception as e:
            logger.warning(f"[PostCallNotifications] Failed to update notification status: {e}")
