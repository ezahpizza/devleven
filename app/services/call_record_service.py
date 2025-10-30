"""Service layer for MongoDB call records."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from pymongo.errors import PyMongoError

from db.mongo import get_calls_collection
from models.call_record_models import CallCompletePayload

logger = logging.getLogger(__name__)


def _normalize_timestamp(value: datetime) -> datetime:
    """Ensure timestamp is timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialize_call_record(document: Dict) -> Dict:
    """Prepare Mongo document for JSON responses."""
    if not document:
        return {}
    serialized = dict(document)
    serialized.pop("_id", None)
    timestamp = serialized.get("timestamp")
    if isinstance(timestamp, datetime):
        serialized["timestamp"] = timestamp.astimezone(timezone.utc)
    return serialized


class CallRecordService:
    """Mongo-backed operations for call records."""
    
    # In-memory store for call metadata (call_sid -> client info)
    _call_metadata: Dict[str, Dict[str, str]] = {}
    
    # In-memory store for linking conversation_id to call_sid
    _conversation_to_call: Dict[str, str] = {}

    @staticmethod
    async def store_call_metadata(call_sid: str, client_name: str, phone_number: str):
        """Store client name and phone number for a call."""
        CallRecordService._call_metadata[call_sid] = {
            "client_name": client_name,
            "phone_number": phone_number
        }
        logger.info(f"[CallRecord] Stored metadata for call_sid={call_sid}: {client_name}")

    @staticmethod
    async def link_conversation_to_call(conversation_id: str, call_sid: str):
        """Link an ElevenLabs conversation_id to a Twilio call_sid."""
        CallRecordService._conversation_to_call[conversation_id] = call_sid
        logger.info(f"[CallRecord] Linked conversation_id={conversation_id} to call_sid={call_sid}")

    @staticmethod
    async def get_call_metadata_by_conversation(conversation_id: str) -> Dict[str, str]:
        """Retrieve metadata using conversation_id."""
        call_sid = CallRecordService._conversation_to_call.get(conversation_id)
        if not call_sid:
            logger.warning(f"[CallRecord] No call_sid found for conversation_id={conversation_id}")
            return {}
        
        metadata = CallRecordService._call_metadata.get(call_sid, {})
        if metadata:
            logger.info(f"[CallRecord] Retrieved metadata for conversation_id={conversation_id}: {metadata}")
        return metadata

    @staticmethod
    async def cleanup_call_metadata(conversation_id: str):
        """Clean up metadata after webhook processing."""
        call_sid = CallRecordService._conversation_to_call.get(conversation_id)
        if call_sid:
            CallRecordService._call_metadata.pop(call_sid, None)
            CallRecordService._conversation_to_call.pop(conversation_id, None)
            logger.info(f"[CallRecord] Cleaned up metadata for conversation_id={conversation_id}")

    @staticmethod
    async def get_call_metadata(call_sid: str) -> Dict[str, str]:
        """Retrieve stored metadata for a call."""
        metadata = CallRecordService._call_metadata.get(call_sid, {})
        if metadata:
            logger.info(f"[CallRecord] Retrieved metadata for call_sid={call_sid}")
        return metadata

    @staticmethod
    async def remove_call_metadata(call_sid: str):
        """Remove metadata after it's been used."""
        if call_sid in CallRecordService._call_metadata:
            del CallRecordService._call_metadata[call_sid]
            logger.info(f"[CallRecord] Removed metadata for call_sid={call_sid}")

    @staticmethod
    async def upsert_call_record(payload: CallCompletePayload) -> Dict:
        """Insert or update a call record."""
        collection = await get_calls_collection()
        record = payload.model_dump()
        record["timestamp"] = _normalize_timestamp(record["timestamp"])
        try:
            result = await collection.update_one(
                {"call_id": record["call_id"]},
                {"$set": record},
                upsert=True,
            )
            document = await collection.find_one(
                {"call_id": record["call_id"]},
                {"_id": 0},
            )
            serialized = _serialize_call_record(document or record)
            return serialized
        except PyMongoError as exc:
            logger.error(f"[MongoDB] Upsert failed for call_id={record['call_id']}: {exc}")
            raise

    @staticmethod
    async def fetch_calls(page: int, page_size: int) -> Tuple[List[Dict], int]:
        """Fetch paginated call records."""
        collection = await get_calls_collection()
        skip = max(page - 1, 0) * page_size
        cursor = (
            collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .skip(skip)
            .limit(page_size)
        )
        records = [_serialize_call_record(doc) async for doc in cursor]
        total = await collection.count_documents({})
        return records, total

    @staticmethod
    async def fetch_call(call_id: str) -> Dict:
        """Fetch a single call record by call_id."""
        collection = await get_calls_collection()
        document = await collection.find_one({"call_id": call_id}, {"_id": 0})
        if not document:
            return {}
        return _serialize_call_record(document)

    @staticmethod
    async def get_summary() -> Dict:
        """Compute summary metrics."""
        collection = await get_calls_collection()
        total_calls = await collection.count_documents({})
        conversions = await collection.count_documents({"conversion_status": True})
        conversion_rate = conversions / total_calls if total_calls else 0.0
        return {
            "total_calls": total_calls,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 4),
        }
