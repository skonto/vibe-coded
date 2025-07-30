#!/usr/bin/env python3
"""
Test script for the MCP Weather Server.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing MCP Weather Server")
    print("=" * 40)
    
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("✅ Successfully connected to MCP server")
                
                # List available tools
                tools_result = await session.list_tools()
                print(f"\n📋 Available tools ({len(tools_result.tools)}):")
                for tool in tools_result.tools:
                    print(f"  • {tool.name}: {tool.description}")
                
                # List available resources
                resources_result = await session.list_resources()
                print(f"\n📦 Available resources ({len(resources_result.resources)}):")
                for resource in resources_result.resources:
                    print(f"  • {resource.uri}: {resource.name or 'No description'}")
                
                # Test weather tool
                print(f"\n🌤️  Testing weather tool...")
                try:
                    weather_result = await session.call_tool("get_weather", arguments={"city": "London"})
                    print("✅ Weather tool executed successfully")
                    
                    # Print structured content if available
                    if hasattr(weather_result, 'structuredContent') and weather_result.structuredContent:
                        weather_data = weather_result.structuredContent
                        print(f"   Temperature: {weather_data.get('temperature', 'N/A')}°C")
                        print(f"   Description: {weather_data.get('description', 'N/A')}")
                        print(f"   City: {weather_data.get('city', 'N/A')}")
                    
                    # Print text content
                    if weather_result.content:
                        for content in weather_result.content:
                            if hasattr(content, 'text'):
                                print(f"   Raw result: {content.text[:100]}...")
                                
                except Exception as e:
                    print(f"❌ Weather tool failed: {e}")
                
                # Test web search tool
                print(f"\n🔍 Testing web search tool...")
                try:
                    search_result = await session.call_tool("web_search", arguments={"query": "Python programming", "max_results": 2})
                    print("✅ Web search tool executed successfully")
                    
                    # Print structured content if available
                    if hasattr(search_result, 'structuredContent') and search_result.structuredContent:
                        search_data = search_result.structuredContent
                        if isinstance(search_data, list):
                            print(f"   Found {len(search_data)} results:")
                            for i, result in enumerate(search_data[:2]):
                                print(f"   {i+1}. {result.get('title', 'No title')}")
                                
                except Exception as e:
                    print(f"❌ Web search tool failed: {e}")
                
                # Test server info resource
                print(f"\n📖 Testing server info resource...")
                try:
                    from pydantic import AnyUrl
                    info_result = await session.read_resource(AnyUrl("server://info"))
                    print("✅ Server info resource read successfully")
                    
                    if info_result.contents:
                        for content in info_result.contents:
                            if hasattr(content, 'text'):
                                info_data = json.loads(content.text)
                                print(f"   Server: {info_data.get('name', 'Unknown')}")
                                print(f"   Version: {info_data.get('version', 'Unknown')}")
                                
                except Exception as e:
                    print(f"❌ Server info resource failed: {e}")
                
                print(f"\n✅ MCP server test completed!")
                
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        return False
    
    return True

def main():
    """Run the MCP server test."""
    success = asyncio.run(test_mcp_server())
    if not success:
        exit(1)

if __name__ == "__main__":
    main() 