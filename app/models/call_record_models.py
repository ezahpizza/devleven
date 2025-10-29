"""Pydantic models for call record payloads and responses."""
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class InsightModel(BaseModel):
    """Structured insights extracted from a call."""

    sentiment: str = Field(..., max_length=64)
    topics: List[str] = Field(default_factory=list)
    duration_sec: int = Field(..., ge=0)

    model_config = ConfigDict(extra="ignore")


class CallCompletePayload(BaseModel):
    """Payload schema for call completion webhook."""

    call_id: str = Field(..., min_length=1, max_length=128)
    client_name: str = Field(..., min_length=1, max_length=255)
    transcript: str = Field(..., min_length=1)
    insights: InsightModel
    conversion_status: bool
    timestamp: datetime

    model_config = ConfigDict(extra="ignore")


class CallRecordResponse(CallCompletePayload):
    """Response schema for call records."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda value: value.isoformat()},
        populate_by_name=True,
    )


class PaginatedCallsResponse(BaseModel):
    """Paginated response wrapper for call records."""

    page: int
    page_size: int
    total: int
    items: List[CallRecordResponse]


class CallSummaryResponse(BaseModel):
    """Summary metrics for dashboard analytics."""

    total_calls: int
    conversions: int
    conversion_rate: float
