"""Pydantic models for call record payloads and responses."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InsightModel(BaseModel):
    """Structured insights extracted from a call."""

    sentiment: str = Field(..., max_length=64)
    topics: List[str] = Field(default_factory=list)
    duration_sec: int = Field(..., ge=0)

    model_config = ConfigDict(extra="ignore")


# ElevenLabs webhook models
class ElevenLabsTranscriptTurn(BaseModel):
    """A single turn in the conversation transcript."""
    role: str
    message: Optional[str] = None
    time_in_call_secs: int = 0
    
    model_config = ConfigDict(extra="ignore")


class ElevenLabsAnalysis(BaseModel):
    """Analysis data from ElevenLabs."""
    call_successful: Optional[str] = None
    transcript_summary: Optional[str] = None
    call_summary_title: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")


class ElevenLabsMetadata(BaseModel):
    """Metadata about the call."""
    call_duration_secs: int = 0
    cost: Optional[int] = None
    termination_reason: Optional[str] = None
    
    model_config = ConfigDict(extra="ignore")


class ElevenLabsConversationData(BaseModel):
    """The main data payload from ElevenLabs post_call_transcription webhook."""
    agent_id: str
    conversation_id: str
    status: str
    transcript: List[ElevenLabsTranscriptTurn]
    metadata: ElevenLabsMetadata
    analysis: Optional[ElevenLabsAnalysis] = None
    
    model_config = ConfigDict(extra="allow")


class ElevenLabsWebhookPayload(BaseModel):
    """Complete ElevenLabs webhook payload structure."""
    type: str
    event_timestamp: int
    data: ElevenLabsConversationData
    
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
