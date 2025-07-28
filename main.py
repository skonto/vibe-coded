import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatGPT with MCP Tools",
    description="A FastAPI application that uses ChatGPT with tool calling capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MCP FastAPI wrapper URL
MCP_BASE_URL = "http://localhost:8000"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[Dict[str, Any]]] = []
    tool_results: Optional[List[str]] = []

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    tool_call: ToolCall
    result: str
    success: bool
    error: Optional[str] = None

async def get_available_tools() -> List[Dict[str, Any]]:
    """Get available tools from the MCP server."""
    logger.info("🔍 Fetching available tools from MCP server...")
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.get(f"{MCP_BASE_URL}/tools")
            response.raise_for_status()
            tools_data = response.json()
            
            # Convert to OpenAI tool format
            openai_tools = []
            for tool in tools_data["tools"]:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })
            
            logger.info(f"✅ Found {len(openai_tools)} tools: {[tool['function']['name'] for tool in openai_tools]}")
            return openai_tools
        except Exception as e:
            logger.error(f"❌ Error getting tools: {e}")
            return []

async def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
    """Call a tool on the MCP server."""
    logger.info(f"🛠️ Calling MCP tool: {tool_name} with arguments: {arguments}")
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(
                f"{MCP_BASE_URL}/tools/call",
                json={"name": tool_name, "arguments": arguments}
            )
            response.raise_for_status()
            result_data = response.json()
            
            logger.info(f"✅ Tool {tool_name} executed successfully: {result_data.get('result', '')}")
            
            return ToolResult(
                tool_call=ToolCall(name=tool_name, arguments=arguments),
                result=result_data.get("result", ""),
                success=result_data.get("success", False),
                error=result_data.get("error")
            )
        except Exception as e:
            logger.error(f"❌ Error calling tool {tool_name}: {e}")
            return ToolResult(
                tool_call=ToolCall(name=tool_name, arguments=arguments),
                result="",
                success=False,
                error=str(e)
            )

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "ChatGPT with MCP Tools API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "Send a message to ChatGPT with tool calling",
            "/tools": "List available tools",
            "/health": "Health check"
        }
    }

@app.get("/tools")
async def list_tools():
    """List all available tools."""
    logger.info("📋 Listing available tools...")
    tools = await get_available_tools()
    return {"tools": tools}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("🏥 Health check requested...")
    # Check if MCP server is running
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.get(f"{MCP_BASE_URL}/health")
            mcp_status = response.json() if response.status_code == 200 else {"status": "unhealthy"}
        except:
            mcp_status = {"status": "unreachable"}
    
    return {
        "status": "healthy",
        "mcp_server": mcp_status,
        "openai_api": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_tools(request: ChatRequest):
    """Chat with ChatGPT using available tools."""
    logger.info(f"💬 Chat request received: '{request.message[:50]}{'...' if len(request.message) > 50 else ''}'")
    
    # Get available tools
    tools = await get_available_tools()
    
    if not tools:
        logger.error("❌ No tools available")
        raise HTTPException(status_code=500, detail="No tools available")
    
    # Prepare conversation history
    messages = []
    
    # Add conversation history
    for msg in request.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})
    
    # Add the current user message
    messages.append({"role": "user", "content": request.message})
    
    logger.info(f"📝 Prepared {len(messages)} messages for OpenAI")
    logger.info(f"🛠️ Available tools for OpenAI: {[tool['function']['name'] for tool in tools]}")
    
    try:
        # Call OpenAI with tool calling
        logger.info("🤖 Calling OpenAI API with tool calling...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        logger.info(f"🤖 OpenAI response received. Content: '{assistant_message.content[:100] if assistant_message.content else 'None'}{'...' if assistant_message.content and len(assistant_message.content) > 100 else ''}'")
        
        tool_calls = []
        tool_results = []
        
        # Handle tool calls if any
        if assistant_message.tool_calls:
            logger.info(f"🔧 OpenAI requested {len(assistant_message.tool_calls)} tool calls")
            for i, tool_call in enumerate(assistant_message.tool_calls):
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🔧 Executing tool call {i+1}/{len(assistant_message.tool_calls)}: {tool_name}({tool_args})")
                
                # Call the MCP tool
                tool_result = await call_mcp_tool(tool_name, tool_args)
                tool_calls.append({
                    "name": tool_name,
                    "arguments": tool_args
                })
                tool_results.append(tool_result.result if tool_result.success else f"Error: {tool_result.error}")
        else:
            logger.info("ℹ️ No tool calls requested by OpenAI")
        
        # If there were tool calls, make another request with the results
        if tool_calls:
            logger.info("🔄 Making follow-up request to OpenAI with tool results...")
            # Add the assistant's message with tool calls
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in assistant_message.tool_calls
                ]
            })
            
            # Add tool results
            for i, tool_call in enumerate(assistant_message.tool_calls):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_results[i]
                })
            
            logger.info(f"📝 Sending follow-up request with {len(messages)} messages to OpenAI...")
            # Get final response
            final_response = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            final_message = final_response.choices[0].message
            response_text = final_message.content or ""
            logger.info(f"🤖 Final OpenAI response: '{response_text[:100]}{'...' if len(response_text) > 100 else ''}'")
        else:
            response_text = assistant_message.content or ""
            logger.info(f"🤖 Direct OpenAI response: '{response_text[:100]}{'...' if len(response_text) > 100 else ''}'")
        
        logger.info("✅ Chat request completed successfully")
        return ChatResponse(
            response=response_text,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        
    except Exception as e:
        logger.error(f"❌ Error calling OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI: {str(e)}")

@app.post("/chat/simple")
async def simple_chat(request: ChatRequest):
    """Simple chat endpoint without tool calling for testing."""
    logger.info(f"💬 Simple chat request: '{request.message[:50]}{'...' if len(request.message) > 50 else ''}'")
    try:
        logger.info("🤖 Calling OpenAI API (simple chat)...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": request.message}]
        )
        
        result = response.choices[0].message.content
        logger.info(f"🤖 Simple chat response: '{result[:100]}{'...' if len(result) > 100 else ''}'")
        
        return {
            "response": result,
            "model": "gpt-4"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in simple chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling OpenAI: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 