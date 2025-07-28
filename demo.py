#!/usr/bin/env python3
"""
Demo script for the MCP + ChatGPT application.
This script demonstrates various API calls and features.
"""

import asyncio
import httpx
import json
import os
from typing import List, Dict, Any

class APIDemo:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.mcp_url = "http://localhost:8000"
        
    async def demo_health_check(self):
        """Demo health check endpoint."""
        print("🏥 Health Check Demo")
        print("-" * 30)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data.get('status')}")
                print(f"🔧 MCP Server: {data.get('mcp_server', {}).get('status', 'unknown')}")
                print(f"🤖 OpenAI API: {data.get('openai_api', 'unknown')}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        print()
    
    async def demo_list_tools(self):
        """Demo listing available tools."""
        print("🛠️ Available Tools Demo")
        print("-" * 30)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                print(f"Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  • {tool['function']['name']}: {tool['function']['description']}")
            else:
                print(f"❌ Failed to get tools: {response.status_code}")
        print()
    
    async def demo_simple_chat(self):
        """Demo simple chat without tools."""
        print("💬 Simple Chat Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping chat demo")
            print()
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/simple",
                json={
                    "message": "Hello! Can you tell me a short joke?",
                    "conversation_history": []
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
            else:
                print(f"❌ Chat failed: {response.status_code}")
        print()
    
    async def demo_calculator_tool(self):
        """Demo calculator tool usage."""
        print("🧮 Calculator Tool Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping tool demo")
            print()
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "What is 25 * 13? Please calculate this for me.",
                    "conversation_history": []
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
                
                tool_calls = data.get("tool_calls", [])
                tool_results = data.get("tool_results", [])
                
                if tool_calls:
                    print("🔧 Tool Calls:")
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  • {tool_call['name']}({json.dumps(tool_call['arguments'])})")
                        if i < len(tool_results):
                            print(f"    Result: {tool_results[i]}")
                else:
                    print("ℹ️  No tool calls made")
            else:
                print(f"❌ Tool demo failed: {response.status_code}")
        print()
    
    async def demo_text_processing(self):
        """Demo text processing tools."""
        print("📝 Text Processing Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping text processing demo")
            print()
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "Convert 'Hello World' to uppercase and then reverse it.",
                    "conversation_history": []
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
                
                tool_calls = data.get("tool_calls", [])
                tool_results = data.get("tool_results", [])
                
                if tool_calls:
                    print("🔧 Tool Calls:")
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  • {tool_call['name']}({json.dumps(tool_call['arguments'])})")
                        if i < len(tool_results):
                            print(f"    Result: {tool_results[i]}")
            else:
                print(f"❌ Text processing demo failed: {response.status_code}")
        print()
    
    async def demo_data_analysis(self):
        """Demo data analysis tools."""
        print("📊 Data Analysis Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping data analysis demo")
            print()
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "Find the sum, average, and maximum of the numbers [10, 25, 15, 30, 20].",
                    "conversation_history": []
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
                
                tool_calls = data.get("tool_calls", [])
                tool_results = data.get("tool_results", [])
                
                if tool_calls:
                    print("🔧 Tool Calls:")
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  • {tool_call['name']}({json.dumps(tool_call['arguments'])})")
                        if i < len(tool_results):
                            print(f"    Result: {tool_results[i]}")
            else:
                print(f"❌ Data analysis demo failed: {response.status_code}")
        print()
    
    async def demo_string_generation(self):
        """Demo string generation tools."""
        print("🔤 String Generation Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping string generation demo")
            print()
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "Generate a random string of length 8 and a pattern string of length 10 with pattern 'xyz'.",
                    "conversation_history": []
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
                
                tool_calls = data.get("tool_calls", [])
                tool_results = data.get("tool_results", [])
                
                if tool_calls:
                    print("🔧 Tool Calls:")
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  • {tool_call['name']}({json.dumps(tool_call['arguments'])})")
                        if i < len(tool_results):
                            print(f"    Result: {tool_results[i]}")
            else:
                print(f"❌ String generation demo failed: {response.status_code}")
        print()
    
    async def demo_conversation_history(self):
        """Demo conversation with history."""
        print("💭 Conversation History Demo")
        print("-" * 30)
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set, skipping conversation demo")
            print()
            return
        
        conversation_history = [
            {"role": "user", "content": "What is 5 + 3?"},
            {"role": "assistant", "content": "The result of 5 + 3 is 8."}
        ]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "Now multiply that result by 2.",
                    "conversation_history": conversation_history
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"🤖 Response: {data.get('response', 'No response')}")
                
                tool_calls = data.get("tool_calls", [])
                tool_results = data.get("tool_results", [])
                
                if tool_calls:
                    print("🔧 Tool Calls:")
                    for i, tool_call in enumerate(tool_calls):
                        print(f"  • {tool_call['name']}({json.dumps(tool_call['arguments'])})")
                        if i < len(tool_results):
                            print(f"    Result: {tool_results[i]}")
            else:
                print(f"❌ Conversation demo failed: {response.status_code}")
        print()
    
    async def run_all_demos(self):
        """Run all demo functions."""
        print("🎬 MCP + ChatGPT Application Demo")
        print("=" * 50)
        print()
        
        # Run demos
        await self.demo_health_check()
        await self.demo_list_tools()
        await self.demo_simple_chat()
        await self.demo_calculator_tool()
        await self.demo_text_processing()
        await self.demo_data_analysis()
        await self.demo_string_generation()
        await self.demo_conversation_history()
        
        print("🎉 Demo completed!")
        print("\n💡 Try the web interface at: http://localhost:8001")
        print("📚 API documentation at: http://localhost:8001/docs")

async def main():
    """Main demo function."""
    demo = APIDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main()) 