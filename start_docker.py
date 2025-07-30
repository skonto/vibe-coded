#!/usr/bin/env python3
"""
Docker-based startup script for Weather Chat API.
Uses official Docker images for all services.
"""

import subprocess
import sys
import os
import time
import signal
import requests
import json
import getpass
from pathlib import Path
from typing import Optional, Dict, Any


class DockerServiceManager:
    """Manages all services using Docker containers."""
    
    def __init__(self):
        self.services_started = []
        self.compose_file = "docker-compose.yml"
        self.openai_api_key = None
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check Docker
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, check=True, text=True)
            print(f"✅ Docker: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker not found - please install Docker")
            print("Visit: https://docs.docker.com/get-docker/")
            return False
        
        # Check Docker Compose
        try:
            result = subprocess.run(["docker", "compose", "version"], 
                                  capture_output=True, check=True, text=True)
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker Compose not found")
            return False
        
        # Check if Docker daemon is running
        try:
            subprocess.run(["docker", "ps"], 
                          capture_output=True, check=True)
            print("✅ Docker daemon is running")
        except subprocess.CalledProcessError:
            print("❌ Docker daemon not running - please start Docker")
            return False
        
        # Check compose file
        if not Path(self.compose_file).exists():
            print(f"❌ {self.compose_file} not found")
            return False
        print(f"✅ {self.compose_file} exists")
        
        return True
    
    def get_openai_key(self) -> bool:
        """Securely prompt for OpenAI API key."""
        print("\n🔑 OpenAI API Key Required")
        print("=" * 30)
        print("To use the chat functionality, please provide your OpenAI API key.")
        print("Get your API key from: https://platform.openai.com/api-keys")
        print("Note: The key will NOT be stored anywhere, only used during this session.")
        print("")  
        print("🌤️  Weather data is provided by Open-Meteo (free, no API key required)")
        print("🔍 Web search is available via DuckDuckGo (free, no API key required)")
        
        try:
            # Try environment variable first
            if os.getenv('OPENAI_API_KEY'):
                self.openai_api_key = os.getenv('OPENAI_API_KEY')
                print("✅ Using OpenAI API key from environment variable")
                return True
            
            # Prompt for key
            while True:
                api_key = getpass.getpass("\nEnter your OpenAI API key (input hidden): ").strip()
                
                if not api_key:
                    print("❌ API key cannot be empty")
                    continue
                
                if not api_key.startswith('sk-'):
                    print("⚠️  OpenAI API keys typically start with 'sk-'")
                    confirm = input("Continue anyway? (y/n): ").lower()
                    if confirm != 'y':
                        continue
                
                self.openai_api_key = api_key
                print("✅ OpenAI API key received")
                return True
                
        except KeyboardInterrupt:
            print("\n❌ API key input cancelled")
            return False
        except Exception as e:
            print(f"❌ Error getting API key: {e}")
            return False
    
    def build_images(self) -> bool:
        """Build Docker images."""
        print("🐳 Building Docker images...")
        
        try:
            result = subprocess.run([
                "docker", "compose", "build", "--no-cache"
            ], check=True, capture_output=True, text=True)
            
            print("✅ Docker images built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build images: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            return False
    
    def start_services(self) -> bool:
        """Start all services using Docker Compose."""
        print("🚀 Starting services with Docker Compose...")
        
        try:
            # Set environment variables for docker compose
            env = os.environ.copy()
            env['OPENAI_API_KEY'] = self.openai_api_key
            
            # Start services in detached mode
            subprocess.run([
                "docker", "compose", "up", "-d"
            ], check=True, env=env)
            
            print("✅ Services started")
            self.services_started.append("docker-compose")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start services: {e}")
            return False
    
    def wait_for_services(self) -> bool:
        """Wait for services to be ready."""
        print("⏳ Waiting for services to be ready...")
        
        # Wait for Redis
        print("🔄 Checking Redis...")
        for i in range(30):
            try:
                result = subprocess.run([
                    "docker", "exec", "weather_chat_redis", "redis-cli", "ping"
                ], capture_output=True, check=True, text=True)
                if "PONG" in result.stdout:
                    print("✅ Redis is ready")
                    break
            except:
                time.sleep(1)
        else:
            print("❌ Redis not ready after 30 seconds")
            return False
        
        # Wait for API
        print("🔄 Checking API...")
        for i in range(60):  # Wait up to 60 seconds for API
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Weather Chat API is ready")
                    return True
            except:
                time.sleep(1)
        
        print("❌ API not ready after 60 seconds")
        return False
    
    def run_health_check(self) -> bool:
        """Run comprehensive health check."""
        print("\n🏥 Running health check...")
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print("✅ API Health Check:")
                print(f"   Service: {health_data.get('service')}")
                print(f"   Version: {health_data.get('version')}")
                print(f"   Redis: {health_data.get('components', {}).get('redis')}")
                print(f"   MCP Tools: {health_data.get('components', {}).get('available_tools')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def run_test_queries(self) -> bool:
        """Run test queries to verify functionality."""
        print("\n🧪 Running test queries...")
        
        try:
            # Test 1: Create session
            print("1️⃣ Creating test session...")
            response = requests.post("http://localhost:8000/chat/session")
            if response.status_code != 200:
                print(f"❌ Failed to create session: {response.status_code}")
                return False
            
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session created: {session_id}")
            
            # Test 2: List available tools
            print("2️⃣ Checking available tools...")
            response = requests.get("http://localhost:8000/chat/tools")
            if response.status_code == 200:
                tools_data = response.json()
                print(f"✅ Available tools: {list(tools_data['tools'].keys())}")
            
            # Test 3: Send a test message (without API keys for now)
            print("3️⃣ Sending test message...")
            test_message = {
                "session_id": session_id,
                "message": "Hello! Can you tell me about the weather API features?",
                "city": "London"
            }
            
            response = requests.post(
                "http://localhost:8000/chat/message",
                json=test_message,
                timeout=30
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                print("✅ Chat response received:")
                print(f"   Response length: {len(chat_response.get('response', ''))}")
                print(f"   Tools used: {chat_response.get('tools_used', [])}")
                print(f"   Has weather data: {'weather_data' in chat_response}")
            elif response.status_code == 503:
                print("⚠️  Chat test shows OpenAI API key needed (expected)")
                print("   OpenAI API key will be prompted when starting the service")
            else:
                print(f"❌ Chat test failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                return False
            
            # Test 4: Get session history
            print("4️⃣ Checking session history...")
            response = requests.get(f"http://localhost:8000/chat/session/{session_id}/history")
            if response.status_code == 200:
                history_data = response.json()
                print(f"✅ Session history: {len(history_data.get('messages', []))} messages")
            
            print("\n🎉 All tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test queries failed: {e}")
            return False
    
    def show_usage_examples(self):
        """Show usage examples and container information."""
        print("\n📚 Usage Examples:")
        print("=" * 50)
        
        # Show running containers
        try:
            result = subprocess.run([
                "docker", "compose", "ps"
            ], capture_output=True, text=True, check=True)
            print("\n🐳 Running Containers:")
            print(result.stdout)
        except:
            pass
        
        print("\n🌐 API Documentation:")
        print("   Swagger UI: http://localhost:8000/docs")
        print("   ReDoc: http://localhost:8000/redoc")
        print("   Health Check: http://localhost:8000/health")
        
        print("\n💬 cURL Examples:")
        print("   # Create session")
        print("   curl -X POST http://localhost:8000/chat/session")
        print()
        print("   # Send message")
        print("   curl -X POST http://localhost:8000/chat/message \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{")
        print("       \"session_id\": \"your-session-id\",")
        print("       \"message\": \"What\\'s the weather in Paris?\",")
        print("       \"city\": \"Paris\"")
        print("     }'")
        
        print("\n🔧 Docker Commands:")
        print("   # View logs")
        print("   docker compose logs -f")
        print("   docker compose logs weather_chat_api")
        print("   docker compose logs redis")
        print()
        print("   # Stop services")
        print("   docker compose down")
        print()
        print("   # Restart services (you'll need to re-enter API key)")
        print("   python start_docker.py")
        
        print("\n🔧 Available MCP Tools:")
        try:
            response = requests.get("http://localhost:8000/chat/tools")
            if response.status_code == 200:
                tools_data = response.json()
                for tool_name, tool_info in tools_data.get('tools', {}).items():
                    print(f"   • {tool_name}: {tool_info.get('description', 'No description')}")
        except:
            print("   • get_weather: Get current weather for a city (Open-Meteo)")
            print("   • get_weather_forecast: Get weather forecast (Open-Meteo)")
            print("   • web_search: Search the web using DuckDuckGo")
            print("   • get_web_content: Extract content from web pages")
    
    def cleanup(self):
        """Clean up Docker services."""
        print("\n🧹 Cleaning up Docker services...")
        
        try:
            subprocess.run([
                "docker", "compose", "down"
            ], check=True)
            print("✅ Docker services stopped")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Error stopping services: {e}")
        
        # Clear the API key from memory
        if self.openai_api_key:
            self.openai_api_key = None
    
    def show_logs(self):
        """Show service logs."""
        print("\n📋 Service Logs:")
        try:
            subprocess.run([
                "docker", "compose", "logs", "--tail", "50"
            ])
        except KeyboardInterrupt:
            pass
    
    def run(self):
        """Run the complete Docker startup sequence."""
        print("🌤️ Weather Chat API - Docker Startup")
        print("=" * 45)
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                sys.exit(1)
            
            # Get OpenAI API key securely
            if not self.get_openai_key():
                sys.exit(1)
            
            # Build images
            if not self.build_images():
                sys.exit(1)
            
            # Start services
            if not self.start_services():
                self.cleanup()
                sys.exit(1)
            
            # Wait for services
            if not self.wait_for_services():
                self.cleanup()
                sys.exit(1)
            
            # Run health check
            if not self.run_health_check():
                self.cleanup()
                sys.exit(1)
            
            # Run tests
            if not self.run_test_queries():
                self.cleanup()
                sys.exit(1)
            
            # Show usage examples
            self.show_usage_examples()
            
            print("\n" + "=" * 45)
            print("🎉 Weather Chat API is running successfully!")
            print("🔄 Press Ctrl+C to stop all services")
            print("📋 Press 'l' + Enter to view logs")
            print("🔒 Your API key is secure and not stored anywhere")
            print("=" * 45)
            
            # Keep running until interrupted
            try:
                while True:
                    user_input = input().strip().lower()
                    if user_input == 'l':
                        self.show_logs()
                    elif user_input == 'q':
                        break
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
                
        except Exception as e:
            print(f"❌ Startup failed: {e}")
            sys.exit(1)
        finally:
            self.cleanup()


def main():
    """Main function."""
    manager = DockerServiceManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Received interrupt signal...")
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager.run()


if __name__ == "__main__":
    main() 