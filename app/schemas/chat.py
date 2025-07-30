from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    city: Optional[str] = Field(None, description="Optional city context")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    session_id: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    weather_data: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = None


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    preferred_city: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class SessionHistory(BaseModel):
    """Session chat history."""
    session_id: str
    messages: List[ChatMessage]
    session_info: SessionInfo


class WeatherData(BaseModel):
    """Weather information."""
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: float  # Changed to float to match Open-Meteo data format
    description: str
    wind_speed: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response structure."""
    error: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow) 