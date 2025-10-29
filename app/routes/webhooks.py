"""Webhook handlers for voice agent call completion."""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from handlers.dashboard_ws import dashboard_manager
from models import CallCompletePayload, CallRecordResponse
from services.call_record_service import CallRecordService

logger = logging.getLogger(__name__)


def register_webhook_routes(app):
    """Register webhook routes."""
    router = APIRouter(tags=["Webhooks"])

    @router.post("/webhook/call_complete")
    async def call_complete_webhook(payload: CallCompletePayload):
        """Persist call completion payloads and trigger dashboard updates."""
        try:
            record = await CallRecordService.upsert_call_record(payload)
            response_model = CallRecordResponse(**record)
            await dashboard_manager.broadcast(
                "call_record_created",
                {
                    "call_id": response_model.call_id,
                    "client_name": response_model.client_name,
                    "timestamp": response_model.timestamp.isoformat(),
                },
            )
            return JSONResponse(
                content={
                    "success": True,
                    "data": response_model.model_dump(mode="json"),
                }
            )
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - network/db errors
            logger.error("[Webhook] call_complete error: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to process webhook")

    app.include_router(router)
