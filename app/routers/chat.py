from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
import logging

from app.schemas.chat import (
    ChatRequest, ChatResponse, SessionHistory, 
    SessionInfo, ErrorResponse
)
from app.services.chat_service import chat_service
from app.services.session_service import session_service
from app.utils.errors import (
    SessionNotFoundException,
    OpenAIException, create_http_exception
)
import subprocess
import json
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one."""
    if session_id:
        try:
            await session_service.get_session(session_id)
            return session_id
        except SessionNotFoundException:
            # Session doesn't exist, create new one with the provided ID
            return await session_service.create_session(session_id)
    else:
        # Create new session with generated ID
        return await session_service.create_session()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message and get AI response with weather context."""
    try:
        # Ensure session exists
        session_id = await get_or_create_session(request.session_id)
        
        # No additional setup needed for MCP integration
        
        # Generate response using chat service
        response = await chat_service.generate_response(
            session_id=session_id,
            user_message=request.message,
            city_hint=request.city
        )
        
        logger.info(f"Generated response for session {session_id}")
        return response
        
    except OpenAIException as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise create_http_exception(503, f"AI service unavailable: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in send_message: {str(e)}")
        raise create_http_exception(500, "Internal server error")


@router.post("/session", response_model=dict)
async def create_session():
    """Create a new chat session."""
    try:
        session_id = await session_service.create_session()
        
        # Register MCP tools for the new session
        # No session-specific setup needed for stdio MCP server
        
        return {
            "session_id": session_id,
            "message": "Session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise create_http_exception(500, "Failed to create session")


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        session_info = await session_service.get_session(session_id)
        return session_info
        
    except SessionNotFoundException:
        raise create_http_exception(404, f"Session {session_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise create_http_exception(500, "Failed to get session information")


@router.get("/session/{session_id}/history", response_model=SessionHistory)
async def get_session_history(session_id: str):
    """Get complete session history."""
    try:
        history = await session_service.get_session_history(session_id)
        return history
        
    except SessionNotFoundException:
        raise create_http_exception(404, f"Session {session_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise create_http_exception(500, "Failed to get session history")


@router.put("/session/{session_id}/preferences")
async def update_preferences(
    session_id: str,
    preferred_city: Optional[str] = None,
    preferences: Optional[dict] = None
):
    """Update user preferences for a session."""
    try:
        await session_service.update_user_preferences(
            session_id=session_id,
            preferred_city=preferred_city,
            preferences=preferences
        )
        
        return {
            "message": "Preferences updated successfully",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise create_http_exception(500, "Failed to update preferences")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and cleanup resources."""
    try:
        # Check if session exists
        await session_service.get_session(session_id)
        
        # Cleanup MCP session
        # No cleanup needed for stdio MCP server
        
        # Note: Redis handles TTL automatically, but we could implement manual cleanup here
        
        return {
            "message": f"Session {session_id} deleted successfully"
        }
        
    except SessionNotFoundException:
        raise create_http_exception(404, f"Session {session_id} not found")
    
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise create_http_exception(500, "Failed to delete session")


@router.get("/tools", response_model=dict)
async def get_available_tools():
    """Get list of available MCP tools."""
    try:
        # Get tools from external MCP server via stdio
        return {"error": "Tool status not implemented for stdio transport"}
        return {
            "tools": tools,
            "total_tools": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        raise create_http_exception(500, "Failed to get available tools")


@router.post("/tools/execute")
async def execute_tools(request: dict):
    """Execute MCP tools directly (for testing/debugging)."""
    try:
        # Note: Direct MCP request handling would require more complex implementation
        # For now, return a simple response
        response = {"error": "Direct MCP requests not implemented via stdio transport"}
        return response
        
    except Exception as e:
        logger.error(f"Error executing tools: {str(e)}")
        raise create_http_exception(500, "Failed to execute tools")


@router.get("/session/{session_id}/summary")
async def get_conversation_summary(session_id: str):
    """Get a summary of the conversation."""
    try:
        summary = await chat_service.get_conversation_summary(session_id)
        return {
            "session_id": session_id,
            "summary": summary
        }
        
    except SessionNotFoundException:
        raise create_http_exception(404, f"Session {session_id} not found")
    
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        raise create_http_exception(500, "Failed to get conversation summary")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Weather Chat API",
                    "mcp_server": "stdio"
    } 