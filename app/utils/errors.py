from fastapi import HTTPException
from typing import Optional, Dict, Any


class WeatherChatException(Exception):
    """Base exception for weather chat application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SessionNotFoundException(WeatherChatException):
    """Raised when a session is not found."""
    pass


class OpenAIException(WeatherChatException):
    """Raised when OpenAI API fails."""
    pass


class MCPException(WeatherChatException):
    """Raised when MCP protocol fails."""
    pass


def create_http_exception(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTP exception with structured error response."""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": message,
            "details": details or {}
        }
    ) 