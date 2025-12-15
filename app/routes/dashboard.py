"""Routes for dashboard APIs and WebSocket broadcasting."""
import logging
import os
import re
from typing import List, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse

from config import Config
from handlers.dashboard_ws import dashboard_manager
from models import (
    CallRecordResponse,
    PaginatedCallsResponse,
    CallSummaryResponse,
    OutboundCallRequest,
)
from models.call_models import BulkOutboundCallRequest, BulkOutboundCallResponse, CallResult, CallRecipient
from services.call_record_service import CallRecordService
from services.twilio_service import TwilioService
from services.elevenlabs_service import ElevenLabsService, ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE_MB
from utils.csv_processor import CSVProcessor

logger = logging.getLogger(__name__)


def validate_phone_number(phone: str) -> bool:
    """Validate E.164 phone number format."""
    pattern = r'^\+?[1-9]\d{1,14}$'
    clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    return bool(re.match(pattern, clean))


def sanitize_phone_number(phone: str) -> str:
    """Clean and format phone number to E.164."""
    clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
    if not clean.startswith('+'):
        if len(clean) == 10:
            clean = '+1' + clean
        elif len(clean) == 11 and clean.startswith('1'):
            clean = '+' + clean
        else:
            clean = '+' + clean
    return clean


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

    @router.post("/api/outbound-calls/bulk", response_model=BulkOutboundCallResponse)
    async def initiate_bulk_calls(request_data: BulkOutboundCallRequest, request: Request):
        """Initiate multiple outbound calls concurrently."""
        if not request_data.recipients:
            raise HTTPException(status_code=400, detail="Recipients list is required")

        try:
            base_url = Config.NGROK_URL or f"https://{request.headers.get('host', 'localhost')}"
            twiml_base_url = f"{base_url}/outbound-call-twiml"

            # Prepare call requests for all recipients
            call_requests = []
            for recipient in request_data.recipients:
                params = {
                    "client_name": recipient.client_name,
                    "phone_number": recipient.number
                }
                twiml_url = f"{twiml_base_url}?{urlencode(params)}"

                call_requests.append({
                    "to_number": recipient.number,
                    "twiml_url": twiml_url,
                    "client_name": recipient.client_name
                })

            # Initiate all calls concurrently
            logger.info(f"[Bulk Call] Initiating {len(call_requests)} concurrent calls")
            results = await twilio_service.initiate_concurrent_calls(call_requests)

            # Process results and broadcast to dashboard
            call_results: List[CallResult] = []
            successful = 0
            failed = 0

            for result in results:
                if result["success"]:
                    successful += 1
                    call_sid = result["call_sid"]
                    
                    # Store metadata for each successful call
                    await CallRecordService.store_call_metadata(
                        call_sid=call_sid,
                        client_name=result["client_name"],
                        phone_number=result["to_number"]
                    )
                    
                    # Broadcast to dashboard
                    payload = {
                        "call_sid": call_sid,
                        "client_name": result["client_name"],
                        "phone_number": result["to_number"],
                        "status": result["status"],
                    }
                    await dashboard_manager.broadcast("call_in_progress", payload)
                    
                    call_results.append(CallResult(
                        success=True,
                        call_sid=call_sid,
                        client_name=result["client_name"],
                        phone_number=result["to_number"]
                    ))
                else:
                    failed += 1
                    call_results.append(CallResult(
                        success=False,
                        call_sid=None,
                        client_name=result["client_name"],
                        phone_number=result["to_number"],
                        error=result.get("error", "Unknown error")
                    ))

            logger.info(f"[Bulk Call] Completed: {successful} successful, {failed} failed")

            return BulkOutboundCallResponse(
                total_requested=len(request_data.recipients),
                successful=successful,
                failed=failed,
                results=call_results
            )

        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover - network errors
            logger.error("[Dashboard] Error initiating bulk calls: %s", exc)
            raise HTTPException(status_code=500, detail="Failed to initiate bulk calls")

    @router.post("/api/outbound-calls/bulk-csv", response_model=BulkOutboundCallResponse)
    async def initiate_bulk_calls_from_csv(
        request: Request,
        file: UploadFile = File(..., description="CSV file with columns: name/client_name and phone/number")
    ):
        """
        Upload CSV file and initiate calls in batches of 5.
        
        CSV file should have columns for name (name, client_name, etc.) 
        and phone number (phone, number, phone_number, etc.)
        """
        # Validate file type
        if not CSVProcessor.validate_csv_format(file.filename or ""):
            raise HTTPException(status_code=400, detail="File must be a CSV file (.csv or .txt)")
        
        # Read file content
        try:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="CSV file is empty")
            
            # Parse CSV
            recipients_data, parse_errors = CSVProcessor.parse_csv(content)
            
            if parse_errors and not recipients_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"CSV parsing errors: {'; '.join(parse_errors[:5])}"  # Show first 5 errors
                )
            
            if not recipients_data:
                raise HTTPException(status_code=400, detail="No valid recipients found in CSV")
            
            # Validate and sanitize phone numbers
            valid_recipients: List[CallRecipient] = []
            validation_errors = []
            
            for idx, recipient_data in enumerate(recipients_data, 1):
                name = recipient_data['client_name'].strip()
                phone = sanitize_phone_number(recipient_data['number'])
                
                # Validate
                if len(name) < 2 or len(name) > 255:
                    validation_errors.append(f"Row {idx}: Invalid name length")
                    continue
                
                if not validate_phone_number(phone):
                    validation_errors.append(f"Row {idx}: Invalid phone number: {recipient_data['number']}")
                    continue
                
                valid_recipients.append(CallRecipient(client_name=name, number=phone))
            
            if not valid_recipients:
                error_msg = "No valid recipients after validation"
                if validation_errors:
                    error_msg += f": {'; '.join(validation_errors[:5])}"
                raise HTTPException(status_code=400, detail=error_msg)
            
            logger.info(f"[CSV Upload] Processing {len(valid_recipients)} valid recipients from CSV")
            if validation_errors:
                logger.warning(f"[CSV Upload] {len(validation_errors)} validation errors: {validation_errors[:3]}")
            
            # Prepare call requests
            base_url = Config.NGROK_URL or f"https://{request.headers.get('host', 'localhost')}"
            twiml_base_url = f"{base_url}/outbound-call-twiml"
            
            call_requests = []
            for recipient in valid_recipients:
                params = {
                    "client_name": recipient.client_name,
                    "phone_number": recipient.number
                }
                twiml_url = f"{twiml_base_url}?{urlencode(params)}"
                
                call_requests.append({
                    "to_number": recipient.number,
                    "twiml_url": twiml_url,
                    "client_name": recipient.client_name
                })
            
            # Initiate calls in batches of 5
            logger.info(f"[CSV Bulk Call] Initiating {len(call_requests)} calls in batches of 5")
            results = await twilio_service.initiate_batched_calls(call_requests, batch_size=5)
            
            # Process results and broadcast to dashboard
            call_results: List[CallResult] = []
            successful = 0
            failed = 0
            
            for result in results:
                if result["success"]:
                    successful += 1
                    call_sid = result["call_sid"]
                    
                    # Store metadata
                    await CallRecordService.store_call_metadata(
                        call_sid=call_sid,
                        client_name=result["client_name"],
                        phone_number=result["to_number"]
                    )
                    
                    # Broadcast to dashboard
                    payload = {
                        "call_sid": call_sid,
                        "client_name": result["client_name"],
                        "phone_number": result["to_number"],
                        "status": result["status"],
                    }
                    await dashboard_manager.broadcast("call_in_progress", payload)
                    
                    call_results.append(CallResult(
                        success=True,
                        call_sid=call_sid,
                        client_name=result["client_name"],
                        phone_number=result["to_number"]
                    ))
                else:
                    failed += 1
                    call_results.append(CallResult(
                        success=False,
                        call_sid=None,
                        client_name=result["client_name"],
                        phone_number=result["to_number"],
                        error=result.get("error", "Unknown error")
                    ))
            
            logger.info(f"[CSV Bulk Call] Completed: {successful} successful, {failed} failed")
            
            return BulkOutboundCallResponse(
                total_requested=len(valid_recipients),
                successful=successful,
                failed=failed,
                results=call_results
            )
        
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("[Dashboard] Error processing CSV bulk calls: %s", exc)
            raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(exc)}")

    # ==================== Knowledge Base / RAG Routes ====================
    
    @router.post("/api/knowledge-base/upload")
    async def upload_knowledge_base_document(
        file: UploadFile = File(..., description="Document file to upload (PDF, TXT, DOC, DOCX, MD)")
    ):
        """
        Upload a document to the ElevenLabs knowledge base, trigger RAG indexing,
        and attach it to the configured agent.
        
        Returns document ID, indexing status, and agent attachment status.
        Use the status endpoint to poll for indexing completion.
        """
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
            )
        
        try:
            # Read file content
            content = await file.read()
            
            # Validate file size
            file_size_mb = len(content) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"
                )
            
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="File is empty")
            
            # Upload document, trigger indexing, and attach to agent
            result = await ElevenLabsService.upload_and_index_document(
                file_content=content,
                filename=file.filename,
                wait_for_completion=False,  # Don't wait, let client poll
                attach_to_agent=True  # Attach to the configured agent
            )
            
            # Broadcast to dashboard
            await dashboard_manager.broadcast("knowledge_base_upload", {
                "document_id": result.get("document_id"),
                "document_name": result.get("document_name"),
                "status": result.get("indexing_status"),
                "progress": result.get("progress_percentage", 0),
                "attached_to_agent": result.get("attached_to_agent", False)
            })
            
            return JSONResponse(content={
                "success": True,
                "message": "Document uploaded, indexing started, and attached to agent",
                "document_id": result.get("document_id"),
                "document_name": result.get("document_name"),
                "indexing_status": result.get("indexing_status"),
                "progress_percentage": result.get("progress_percentage", 0),
                "attached_to_agent": result.get("attached_to_agent", False),
                "agent_id": result.get("agent_id"),
                "agent_attachment_error": result.get("agent_attachment_error")
            })
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[Knowledge Base] Error uploading document: {exc}")
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(exc)}")
    
    @router.get("/api/knowledge-base/status/{document_id}")
    async def get_knowledge_base_indexing_status(document_id: str):
        """
        Get the RAG indexing status for a specific document.
        
        Poll this endpoint to track indexing progress.
        """
        try:
            status_data = await ElevenLabsService.get_rag_index_status(document_id)
            
            return JSONResponse(content={
                "document_id": document_id,
                "status": status_data.get("status"),
                "progress_percentage": status_data.get("progress_percentage", 0),
                "model": status_data.get("model")
            })
            
        except Exception as exc:
            logger.error(f"[Knowledge Base] Error getting status for {document_id}: {exc}")
            raise HTTPException(status_code=500, detail=f"Failed to get indexing status: {str(exc)}")
    
    @router.get("/api/knowledge-base/documents")
    async def list_knowledge_base_documents(
        page_size: int = Query(50, ge=1, le=100),
        search: Optional[str] = Query(None, description="Search query for document names")
    ):
        """
        List all documents in the account's knowledge base.
        """
        try:
            result = await ElevenLabsService.list_knowledge_base_documents(
                page_size=page_size,
                search=search
            )
            
            # Transform documents for frontend
            documents = []
            for doc in result.get("documents", []):
                documents.append({
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "type": doc.get("type"),
                    "created_at": doc.get("metadata", {}).get("created_at_unix_secs"),
                    "size_bytes": doc.get("metadata", {}).get("size_bytes"),
                    "supported_usages": doc.get("supported_usages", [])
                })
            
            return JSONResponse(content={
                "documents": documents,
                "has_more": result.get("has_more", False)
            })
            
        except Exception as exc:
            logger.error(f"[Knowledge Base] Error listing documents: {exc}")
            raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(exc)}")
    
    @router.get("/api/knowledge-base/agent-documents")
    async def get_agent_knowledge_base_documents():
        """
        List documents attached to the configured agent's knowledge base.
        
        This returns only documents that are actively being used by the agent for RAG.
        """
        try:
            documents = await ElevenLabsService.get_agent_knowledge_base()
            
            return JSONResponse(content={
                "agent_id": Config.ELEVENLABS_AGENT_ID,
                "documents": documents,
                "count": len(documents)
            })
            
        except Exception as exc:
            logger.error(f"[Knowledge Base] Error getting agent documents: {exc}")
            raise HTTPException(status_code=500, detail=f"Failed to get agent documents: {str(exc)}")
    
    @router.get("/api/knowledge-base/document/{document_id}")
    async def get_knowledge_base_document(document_id: str):
        """
        Get details of a specific document in the knowledge base.
        """
        try:
            doc = await ElevenLabsService.get_knowledge_base_document(document_id)
            
            return JSONResponse(content={
                "id": doc.get("id"),
                "name": doc.get("name"),
                "type": doc.get("type"),
                "created_at": doc.get("metadata", {}).get("created_at_unix_secs"),
                "size_bytes": doc.get("metadata", {}).get("size_bytes"),
                "supported_usages": doc.get("supported_usages", [])
            })
            
        except Exception as exc:
            logger.error(f"[Knowledge Base] Error getting document {document_id}: {exc}")
            raise HTTPException(status_code=500, detail=f"Failed to get document: {str(exc)}")

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
