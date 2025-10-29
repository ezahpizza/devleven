"""Models for call-related requests and responses."""
from pydantic import BaseModel, Field


class OutboundCallRequest(BaseModel):
    """Request model for initiating outbound calls."""
    number: str = Field(..., description="Phone number to call in E.164 format")
    client_name: str = Field(..., description="Name of the client to personalize the greeting")
