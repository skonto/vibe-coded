import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from mcp_server import mcp_server

app = FastAPI(title="MCP FastAPI Wrapper", version="1.0.0")

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    result: str
    success: bool
    error: Optional[str] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class ListToolsResponse(BaseModel):
    tools: List[ToolInfo]

@app.get("/tools", response_model=ListToolsResponse)
async def list_tools():
    """List all available tools."""
    try:
        tools_data = mcp_server.list_tools()
        tools = []
        for tool_data in tools_data:
            tools.append(ToolInfo(
                name=tool_data["name"],
                description=tool_data["description"],
                input_schema=tool_data["inputSchema"]
            ))
        return ListToolsResponse(tools=tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Call a specific tool."""
    try:
        result = await mcp_server.call_tool(request.name, request.arguments)
        
        # Extract text content from result
        result_text = ""
        if result.get("content"):
            for item in result["content"]:
                if item.get("type") == "text":
                    result_text += item.get("text", "")
        
        success = not result.get("isError", False)
        error = None if success else result_text
        
        return ToolCallResponse(
            result=result_text if success else "",
            success=success,
            error=error
        )
    except Exception as e:
        return ToolCallResponse(result="", success=False, error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mcp_server_running": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 