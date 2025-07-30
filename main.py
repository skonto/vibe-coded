from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers.chat import router as chat_router
from app.services.session_service import session_service
from app.utils.errors import (
    WeatherChatException, SessionNotFoundException,
    OpenAIException, MCPException
)
import subprocess
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Weather Chat API...")
    
    # Initialize Redis connection
    await session_service.init_redis()
    logger.info("Redis connection initialized")
    
    # Check MCP server availability
    try:
        result = subprocess.run(
            ["python", "mcp_server.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        if result.returncode == 0:
            logger.info("MCP server script is available")
        else:
            logger.warning("MCP server script test failed")
    except Exception as e:
        logger.warning(f"Could not test MCP server: {e}")
    logger.info("Weather Chat API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Weather Chat API...")
    await session_service.close_redis()
    logger.info("Weather Chat API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.title,
    version=settings.version,
    description="""
    A FastAPI application that uses ChatGPT to provide weather information with session-based chat history.
    Features MCP (Message Control Protocol) server integration for web access and tool calling.
    
    ## Features
    - 🤖 ChatGPT integration for natural language conversations
    - 🌤️ **Free weather data** from Open-Meteo (no API key required!)
    - 💬 Session-based chat history with Redis
    - 🔧 MCP server with web search and weather tools
    - 🧠 Context-aware responses based on user preferences
    - 🔄 Tool calling for enhanced functionality
    
    ## Getting Started
    1. Create a session: `POST /chat/session`
    2. Send messages: `POST /chat/message`
    3. View history: `GET /chat/session/{session_id}/history`
    """,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)

# Global exception handlers
@app.exception_handler(WeatherChatException)
async def weather_chat_exception_handler(request, exc: WeatherChatException):
    """Handle custom weather chat exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": "WeatherChatException"
        }
    )

@app.exception_handler(SessionNotFoundException)
async def session_not_found_handler(request, exc: SessionNotFoundException):
    """Handle session not found exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": "SessionNotFoundException"
        }
    )

@app.exception_handler(OpenAIException)
async def openai_exception_handler(request, exc: OpenAIException):
    """Handle OpenAI exceptions."""
    return JSONResponse(
        status_code=503,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": "OpenAIException"
        }
    )

@app.exception_handler(MCPException)
async def mcp_exception_handler(request, exc: MCPException):
    """Handle MCP exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": "MCPException"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Weather Chat API",
        "version": settings.version,
        "description": "AI-powered weather chat with session management",
        "features": [
            "ChatGPT integration",
            "Weather data from Open-Meteo (free, accurate, no API key required)", 
            "Session-based chat history",
            "MCP server with web access",
            "Tool calling capabilities"
        ],
        "endpoints": {
            "create_session": "POST /chat/session",
            "send_message": "POST /chat/message", 
            "get_history": "GET /chat/session/{session_id}/history",
            "available_tools": "GET /chat/tools",
            "health_check": "GET /chat/health"
        },
        "mcp_script": "mcp_server.py"
    }

@app.get("/health")
async def health_check():
    """Application health check."""
    try:
        # Check Redis connection
        await session_service.init_redis()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": settings.title,
        "version": settings.version,
        "components": {
            "redis": redis_status,
                    "mcp_server": "stdio",
        "mcp_script": "mcp_server.py"
        }
    }

# Development server
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    ) 