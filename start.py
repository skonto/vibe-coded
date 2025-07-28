#!/usr/bin/env python3
"""
Startup script for the MCP + ChatGPT application.
This script starts both the MCP FastAPI wrapper and the main ChatGPT application.
"""

import asyncio
import subprocess
import sys
import time
import os
import signal
from pathlib import Path

class ApplicationManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n🛑 Shutting down applications...")
        self.running = False
        self.stop_all()
        sys.exit(0)
    
    def start_mcp_wrapper(self):
        """Start the MCP FastAPI wrapper."""
        print("🚀 Starting MCP FastAPI wrapper on port 8000...")
        process = subprocess.Popen([
            sys.executable, "mcp_fastapi_wrapper.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("MCP Wrapper", process))
        return process
    
    def start_main_app(self):
        """Start the main ChatGPT application."""
        print("🚀 Starting main ChatGPT application on port 8001...")
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("Main App", process))
        return process
    
    def stop_all(self):
        """Stop all running processes."""
        for name, process in self.processes:
            print(f"🛑 Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
    
    def check_health(self):
        """Check if all services are healthy."""
        import httpx
        
        try:
            # Check MCP wrapper
            with httpx.Client(timeout=5) as client:
                response = client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("✅ MCP Wrapper is healthy")
                else:
                    print("❌ MCP Wrapper is not responding")
                    return False
                
                # Check main app
                response = client.get("http://localhost:8001/health")
                if response.status_code == 200:
                    print("✅ Main App is healthy")
                else:
                    print("❌ Main App is not responding")
                    return False
                    
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        return True
    
    def run(self):
        """Run the complete application."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🎯 Starting MCP + ChatGPT Application")
        print("=" * 50)
        
        # Check if OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Warning: OPENAI_API_KEY environment variable is not set")
            print("   Please set it before using the application:")
            print("   export OPENAI_API_KEY='your-api-key-here'")
            print()
        
        # Start MCP wrapper
        mcp_process = self.start_mcp_wrapper()
        time.sleep(3)  # Give it time to start
        
        # Start main app
        main_process = self.start_main_app()
        time.sleep(3)  # Give it time to start
        
        print("\n🎉 Applications started!")
        print("📱 Web Interface: http://localhost:8001")
        print("🔧 MCP API: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8001/docs")
        print("\nPress Ctrl+C to stop all applications")
        print("=" * 50)
        
        # Wait for processes and monitor health
        try:
            while self.running:
                # Check if processes are still running
                if mcp_process.poll() is not None:
                    print("❌ MCP Wrapper process died")
                    break
                
                if main_process.poll() is not None:
                    print("❌ Main App process died")
                    break
                
                # Health check every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.check_health()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        finally:
            self.stop_all()
            print("👋 All applications stopped")

def main():
    """Main entry point."""
    # Check if required files exist
    required_files = ["mcp_server.py", "mcp_fastapi_wrapper.py", "main.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        sys.exit(1)
    
    # Check if static directory exists
    if not Path("static").exists():
        print("📁 Creating static directory...")
        Path("static").mkdir(exist_ok=True)
    
    # Start the application manager
    manager = ApplicationManager()
    manager.run()

if __name__ == "__main__":
    main() 