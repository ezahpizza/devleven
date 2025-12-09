"""Webhook handlers for voice agent call completion."""
import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from config import Config
from handlers.dashboard_ws import dashboard_manager
from models import (
    CallCompletePayload, 
    CallRecordResponse, 
    ElevenLabsWebhookPayload,
    InsightModel
)
from services.call_record_service import CallRecordService
from services.gemini_service import GeminiService
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
                
                # Determine sentiment based on call success
                sentiment = "positive"
                if elevenlabs_payload.data.analysis:
                    if elevenlabs_payload.data.analysis.call_successful == "success":
                        sentiment = "positive"
                    elif elevenlabs_payload.data.analysis.call_successful == "failure":
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"
                
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
                        sentiment=sentiment,
                        topics=topics,
                        duration_sec=elevenlabs_payload.data.metadata.call_duration_secs
                    ),
                    conversion_status=conversion_status,
                    timestamp=datetime.fromtimestamp(elevenlabs_payload.event_timestamp)
                )
                
                # Generate AI summary and extract follow-up date using Gemini
                try:
                    summary, follow_up_date = await GeminiService.analyze_transcript(transcript_text.strip())
                    payload.summary = summary
                    payload.follow_up_date = follow_up_date
                    logger.info(f"[Webhook] Gemini analysis complete - summary: {summary[:50]}..., follow_up: {follow_up_date}")
                except Exception as gemini_error:
                    logger.warning(f"[Webhook] Gemini analysis failed, continuing without summary: {gemini_error}")
                    payload.summary = None
                    payload.follow_up_date = None
                
            except Exception as e:
                logger.error(f"[Webhook] Failed to parse payload: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid payload structure: {e}")
            
            # Process the webhook
            record = await CallRecordService.upsert_call_record(payload)
            response_model = CallRecordResponse(**record)
            
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

    app.include_router(router)
