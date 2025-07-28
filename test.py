#!/usr/bin/env python3
"""
Test script for the MCP + ChatGPT application.
This script tests all components to ensure they're working correctly.
"""

import asyncio
import httpx
import json
import os
import sys
import time
from pathlib import Path

class ApplicationTester:
    def __init__(self):
        self.mcp_base_url = "http://localhost:8000"
        self.main_base_url = "http://localhost:8001"
        self.results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        self.results.append((test_name, success, message))
    
    async def test_mcp_wrapper_health(self):
        """Test if the MCP wrapper is responding."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.mcp_base_url}/health")
                if response.status_code == 200:
                    self.log_test("MCP Wrapper Health", True)
                    return True
                else:
                    self.log_test("MCP Wrapper Health", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("MCP Wrapper Health", False, str(e))
            return False
    
    async def test_mcp_tools_list(self):
        """Test if the MCP wrapper can list tools."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.mcp_base_url}/tools")
                if response.status_code == 200:
                    data = response.json()
                    tools_count = len(data.get("tools", []))
                    self.log_test("MCP Tools List", True, f"Found {tools_count} tools")
                    return True
                else:
                    self.log_test("MCP Tools List", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("MCP Tools List", False, str(e))
            return False
    
    async def test_mcp_tool_call(self):
        """Test if the MCP wrapper can call a tool."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{self.mcp_base_url}/tools/call",
                    json={
                        "name": "calculator",
                        "arguments": {
                            "operation": "add",
                            "a": 5,
                            "b": 3
                        }
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and "8" in data.get("result", ""):
                        self.log_test("MCP Tool Call", True, "Calculator tool working")
                        return True
                    else:
                        self.log_test("MCP Tool Call", False, f"Unexpected result: {data}")
                        return False
                else:
                    self.log_test("MCP Tool Call", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("MCP Tool Call", False, str(e))
            return False
    
    async def test_main_app_health(self):
        """Test if the main application is responding."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.main_base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    self.log_test("Main App Health", True, f"Status: {data.get('status')}")
                    return True
                else:
                    self.log_test("Main App Health", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("Main App Health", False, str(e))
            return False
    
    async def test_main_app_tools(self):
        """Test if the main application can list tools."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.main_base_url}/tools")
                if response.status_code == 200:
                    data = response.json()
                    tools_count = len(data.get("tools", []))
                    self.log_test("Main App Tools", True, f"Found {tools_count} tools")
                    return True
                else:
                    self.log_test("Main App Tools", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("Main App Tools", False, str(e))
            return False
    
    async def test_openai_integration(self):
        """Test if OpenAI integration is working."""
        if not os.getenv("OPENAI_API_KEY"):
            self.log_test("OpenAI Integration", False, "OPENAI_API_KEY not set")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.main_base_url}/chat/simple",
                    json={
                        "message": "Hello",
                        "conversation_history": []
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        self.log_test("OpenAI Integration", True, "Simple chat working")
                        return True
                    else:
                        self.log_test("OpenAI Integration", False, "No response in data")
                        return False
                else:
                    self.log_test("OpenAI Integration", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("OpenAI Integration", False, str(e))
            return False
    
    async def test_tool_calling(self):
        """Test if tool calling with ChatGPT is working."""
        if not os.getenv("OPENAI_API_KEY"):
            self.log_test("Tool Calling", False, "OPENAI_API_KEY not set")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.main_base_url}/chat",
                    json={
                        "message": "Calculate 10 + 5",
                        "conversation_history": []
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data and "tool_calls" in data:
                        self.log_test("Tool Calling", True, "Tool calling working")
                        return True
                    else:
                        self.log_test("Tool Calling", False, "No tool calls in response")
                        return False
                else:
                    self.log_test("Tool Calling", False, f"Status code: {response.status_code}")
                    return False
        except Exception as e:
            self.log_test("Tool Calling", False, str(e))
            return False
    
    def print_summary(self):
        """Print a summary of all test results."""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        for test_name, success, message in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if message:
                print(f"   {message}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The application is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 Running Application Tests")
        print("="*50)
        
        # Test MCP wrapper
        await self.test_mcp_wrapper_health()
        await self.test_mcp_tools_list()
        await self.test_mcp_tool_call()
        
        # Test main application
        await self.test_main_app_health()
        await self.test_main_app_tools()
        
        # Test OpenAI integration
        await self.test_openai_integration()
        await self.test_tool_calling()
        
        # Print summary
        self.print_summary()

async def main():
    """Main test function."""
    print("🚀 Starting application tests...")
    print("Make sure both services are running:")
    print("  - MCP Wrapper: http://localhost:8000")
    print("  - Main App: http://localhost:8001")
    print()
    
    # Wait a moment for services to be ready
    print("⏳ Waiting for services to be ready...")
    await asyncio.sleep(2)
    
    tester = ApplicationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 