"""Routes for dashboard APIs and WebSocket broadcasting."""
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from config import Config
from handlers.dashboard_ws import dashboard_manager
from models import (
    CallRecordResponse,
    PaginatedCallsResponse,
    CallSummaryResponse,
    OutboundCallRequest,
)
from services.call_record_service import CallRecordService
from services.twilio_service import TwilioService

logger = logging.getLogger(__name__)


def register_dashboard_routes(app):
    """Register dashboard REST and WebSocket endpoints."""
    router = APIRouter(tags=["Dashboard"])
    twilio_service = TwilioService()

    @router.get("/api/calls", response_model=PaginatedCallsResponse)
    async def list_calls(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        records, total = await CallRecordService.fetch_calls(page, page_size)
        items = [CallRecordResponse(**record) for record in records]
        return PaginatedCallsResponse(
            page=page,
            page_size=page_size,
            total=total,
            items=items,
        )

    @router.get("/api/calls/summary", response_model=CallSummaryResponse)
    async def get_calls_summary():
        summary = await CallRecordService.get_summary()
        return CallSummaryResponse(**summary)

    @router.get("/api/call/{call_id}", response_model=CallRecordResponse)
    async def get_call(call_id: str):
        record = await CallRecordService.fetch_call(call_id)
        if not record:
            raise HTTPException(status_code=404, detail="Call not found")
        return CallRecordResponse(**record)

    @router.post("/api/initiate_call")
    async def initiate_call(request_data: OutboundCallRequest, request: Request):
        if not request_data.number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        if not request_data.client_name:
            raise HTTPException(status_code=400, detail="Client name is required")

        try:
            base_url = Config.NGROK_URL or f"https://{request.headers.get('host', 'localhost')}"
            twiml_url = f"{base_url}/outbound-call-twiml"
            params = {
                "client_name": request_data.client_name,
                "phone_number": request_data.number,
            }
            twiml_url_with_params = f"{twiml_url}?{urlencode(params)}"

            call_info = await twilio_service.initiate_call(
                to_number=request_data.number,
                twiml_url=twiml_url_with_params,
            )

            # Store client name for later retrieval in webhook
            call_sid = call_info.get("call_sid")
            await CallRecordService.store_call_metadata(
                call_sid=call_sid,
                client_name=request_data.client_name,
                phone_number=request_data.number
            )

            payload = {
                "call_sid": call_info.get("call_sid"),
                "client_name": request_data.client_name,
                "phone_number": request_data.number,
                "status": call_info.get("status"),
            }
            await dashboard_manager.broadcast("call_in_progress", payload)

            return JSONResponse(
                content={
                    "success": True,
                    "message": "Call initiated",
                    "callSid": call_info.get("call_sid"),
                    "clientName": request_data.client_name,
                    "phoneNumber": request_data.number,
                }
            )
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("[Dashboard] Error initiating call: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to initiate call")

    @router.websocket("/ws/dashboard")
    async def dashboard_websocket(websocket: WebSocket):
        await dashboard_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("[Dashboard] WebSocket disconnected")
        except Exception as exc:  # pragma: no cover - client errors
            logger.debug("[Dashboard] WebSocket error: %s", exc)
        finally:
            await dashboard_manager.disconnect(websocket)

    app.include_router(router)
