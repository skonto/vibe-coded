# Weather Chat API

A FastAPI-based weather chat application that uses OpenAI's GPT models to provide conversational weather information. The app integrates with **Open-Meteo** (completely free, no API key required) for weather data and includes web search capabilities through an MCP (Message Control Protocol) server.

## 🚀 Quick Start (Docker - Recommended)

The easiest way to get started is with Docker:

```bash
# Clone and enter the project
git clone <your-repo-url>
cd weather-chat-api

# Start everything (you'll be prompted only for OpenAI API key)
make docker-start
```

That's it! The system will:
- ✅ Prompt for your OpenAI API key (securely, not stored)
- 🐳 Build and start Redis + API in Docker containers  
- 🌤️ Use Open-Meteo for weather data (free, no API key needed)
- 🔍 Enable web search via DuckDuckGo (free, no API key needed)
- 🧪 Run health checks and test queries
- 📋 Show you example API calls

## ✨ Key Features

### 🔒 **Secure & Simple**
- **Only OpenAI API key required** - prompted securely at runtime
- **No API keys stored** in files or environment variables
- **Free weather data** from Open-Meteo (no registration needed)
- **Free web search** via DuckDuckGo (no registration needed)

### 🎯 **Smart Conversations**
- **Session-based chat history** with Redis storage
- **Context-aware responses** that remember user preferences
- **Preferred city detection** from conversation history
- **Multi-turn conversations** with weather context

### 🌐 **Comprehensive Weather Data**
- **Current weather** for any city worldwide
- **Multi-day forecasts** (up to 16 days)
- **High-accuracy data** from national weather services via Open-Meteo
- **Global coverage** with geocoding support

### 🔗 **MCP Integration**
- **Tool calling** with OpenAI function calling
- **Web search** for weather-related information
- **Web content extraction** from URLs
- **Extensible architecture** for adding new tools

## 🛠️ Available Setup Methods

### 1. Docker (Recommended)
```bash
make docker-start    # Start with Docker Compose
make docker-logs     # View container logs
make docker-down     # Stop containers
```

### 2. Virtual Environment
```bash
make setup-venv      # Create venv and install dependencies
make start-venv      # Start with virtual environment
```

### 3. System Installation
```bash
make install         # Install system dependencies
make dev            # Start in development mode
```

## 📡 API Endpoints

### Chat Endpoints
- `POST /chat/session` - Create new chat session
- `POST /chat/message` - Send message to chat
- `GET /chat/session/{session_id}` - Get session info
- `GET /chat/session/{session_id}/history` - Get chat history

### Utility Endpoints
- `GET /chat/tools` - List available MCP tools
- `GET /health` - Health check
- `GET /` - API information

## 🔧 MCP Tools Available

The system includes these built-in tools:

1. **get_weather** - Current weather for any city (Open-Meteo)
2. **get_weather_forecast** - Multi-day weather forecast (Open-Meteo)  
3. **web_search** - Search the web using DuckDuckGo
4. **get_web_content** - Extract content from web pages

## 💬 Example Usage

### Start a Chat Session
```bash
curl -X POST http://localhost:8000/chat/session
```

### Send a Weather Query
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "What is the weather like in Paris?",
    "city": "Paris"
  }'
```

### Example Response
```json
{
  "response": "The current weather in Paris is partly cloudy with a temperature of 18°C (feels like 17°C). Humidity is at 65% with light winds at 12 km/h. It's a pleasant day - perfect for a walk outside!",
  "session_id": "your-session-id",
  "weather_data": {
    "city": "Paris",
    "temperature": 18.0,
    "feels_like": 17.0,
    "humidity": 65,
    "description": "partly cloudy",
    "wind_speed": 12.0
  },
  "tools_used": ["get_weather"]
}
```

## 🌍 Weather Data Source

This application uses **Open-Meteo**, an open-source weather API that:

- ✅ **Completely free** for non-commercial use
- ✅ **No API key required** - works immediately  
- ✅ **High accuracy** - uses data from national weather services
- ✅ **Global coverage** - weather data for anywhere in the world
- ✅ **Up to 16-day forecasts** - comprehensive forecast data
- ✅ **Open source** - transparent and reliable

Learn more at: https://open-meteo.com

## 🔐 Security Features

- **Runtime-only API key storage** - OpenAI key prompted securely, never stored
- **No sensitive data in Docker images** - `.env` files excluded via `.dockerignore`
- **Environment variable injection** - API keys passed to containers at runtime
- **Session isolation** - each user gets isolated chat sessions
- **Input validation** - Pydantic models for request/response validation

## 📊 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   Session Store  │────│      Redis      │
│                 │    │     (Redis)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ├─────────────────┐
         │                 │
┌─────────────────┐    ┌──────────────────┐
│   OpenAI API    │    │   MCP Server     │
│  (Chat/Tools)   │    │  (Tool Calling)  │
└─────────────────┘    └──────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌──────────┐ ┌─────────┐ ┌─────────┐
            │Open-Meteo│ │DuckDuck │ │Web Fetch│
            │(Weather) │ │Go Search│ │ Tools   │
            └──────────┘ └─────────┘ └─────────┘
```

## 🔧 Development

### Requirements
- Python 3.11+
- Docker & Docker Compose (for containerized setup)
- Redis (for local development)

### Environment Variables
Only one environment variable is required:
- `OPENAI_API_KEY` - Your OpenAI API key (prompted at runtime)

All other settings have sensible defaults:
- `REDIS_URL` - defaults to `redis://localhost:6379`
- `SECRET_KEY` - has a default value (change in production)
- `DEBUG` - defaults to `True`

### Development Commands
```bash
# Development setup
make dev-setup       # Setup development environment (uses Docker)

# Docker commands  
make docker-build    # Build Docker images
make docker-up       # Start services in background
make docker-logs     # View logs
make docker-down     # Stop and remove containers

# Virtual environment commands
make setup-venv      # Create virtual environment and install deps
make run-venv        # Run API in virtual environment

# Testing and utilities
make test           # Run tests (when implemented)
make clean          # Clean up temporary files
```

## 📚 Project Structure

```
weather-chat-api/
├── app/                    # FastAPI application
│   ├── core/              # Core configuration and settings
│   ├── services/          # Business logic services
│   ├── schemas/           # Pydantic models
│   ├── routers/           # API route definitions
│   └── utils/             # Utility functions and error handling
├── mcp/                   # Message Control Protocol implementation
│   ├── models.py          # MCP data models
│   ├── protocol.py        # Protocol parsing and routing
│   ├── server.py          # MCP server implementation
│   └── tools/             # MCP tool implementations
├── main.py                # FastAPI app entry point
├── docker-compose.yml     # Docker services configuration
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
├── Makefile              # Development commands
└── start_docker.py       # Docker startup script
```

## 🆘 Troubleshooting

### Docker Issues
```bash
# Check if containers are running
docker compose ps

# View container logs
docker compose logs weather_chat_api
docker compose logs redis

# Restart services
docker compose restart

# Complete reset
docker compose down
docker system prune -f
python start_docker.py
```

### API Key Issues
- Make sure your OpenAI API key starts with `sk-`
- Check your OpenAI account has sufficient credits
- The key is only prompted once per session - restart if needed

### Weather Data Issues
- Open-Meteo requires no setup and should work immediately
- Check internet connectivity if weather requests fail
- Try different city names if geocoding fails

### Redis Connection Issues
```bash
# For Docker setup - Redis should start automatically
docker compose logs redis

# For local setup - ensure Redis is running
redis-cli ping  # Should return "PONG"
```

## 📄 License

This project is open source. The weather data from Open-Meteo is provided under CC BY 4.0 license.

## 🤝 Contributing

Contributions are welcome! This project demonstrates:
- FastAPI best practices
- OpenAI function calling
- Docker containerization
- Redis session management
- MCP protocol implementation
- Secure API key handling

Feel free to open issues or submit pull requests.

## 🙏 Acknowledgments

- **Open-Meteo** for providing free, high-quality weather data
- **OpenAI** for GPT models and function calling capabilities
- **FastAPI** for the excellent web framework
- **Redis** for fast session storage 