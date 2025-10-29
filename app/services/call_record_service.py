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

    @staticmethod
    async def upsert_call_record(payload: CallCompletePayload) -> Dict:
        """Insert or update a call record."""
        collection = await get_calls_collection()
        record = payload.model_dump()
        record["timestamp"] = _normalize_timestamp(record["timestamp"])
        try:
            await collection.update_one(
                {"call_id": record["call_id"]},
                {"$set": record},
                upsert=True,
            )
            document = await collection.find_one(
                {"call_id": record["call_id"]},
                {"_id": 0},
            )
            serialized = _serialize_call_record(document or record)
            logger.info(f"[Calls] Upserted call_id={record['call_id']}")
            return serialized
        except PyMongoError as exc:
            logger.error(f"[Calls] Upsert failed: {exc}")
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
