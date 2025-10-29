"""Async MongoDB client setup and helpers."""
import asyncio
import logging
from typing import Optional

from pymongo import DESCENDING, AsyncMongoClient
from pymongo.errors import PyMongoError
from config import Config

logger = logging.getLogger(__name__)

_client: Optional[AsyncMongoClient] = None
_calls_collection = None
_init_lock = asyncio.Lock()


async def init_mongo():
    """Initialize MongoDB client and ensure indexes."""
    Config.validate_mongo_config()
    async with _init_lock:
        global _client, _calls_collection
        if _client is not None:
            return _calls_collection

        try:
            _client = AsyncMongoClient(Config.MONGO_URI, appname="eleventwilio")
            database = _client.voice_agent
            _calls_collection = database.calls
            await _calls_collection.create_index("call_id", unique=True)
            await _calls_collection.create_index([("timestamp", DESCENDING)])
            logger.info("[MongoDB] Connected and indexes ensured")
        except PyMongoError as exc:
            logger.error(f"[MongoDB] Initialization failed: {exc}")
            raise
    return _calls_collection


async def get_calls_collection():
    """Return the calls collection, initializing if required."""
    global _calls_collection
    if _calls_collection is None:
        await init_mongo()
    return _calls_collection


async def close_mongo():
    """Close MongoDB client."""
    global _client, _calls_collection
    if _client is not None:
        await _client.close()
        _client = None
        _calls_collection = None
        logger.info("[MongoDB] Connection closed")
