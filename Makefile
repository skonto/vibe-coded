# Weather Chat API Makefile

.PHONY: help docker-start docker-build docker-up docker-down docker-logs docker-clean clean test dev-setup

# Default target
help:
	@echo "Weather Chat API - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "🐳 Docker (Recommended):"
	@echo "  docker-start   - Complete Docker startup (prompts for OpenAI key)"
	@echo "  docker-build   - Build Docker images"
	@echo "  docker-up      - Start with Docker Compose"
	@echo "  docker-down    - Stop Docker services"
	@echo "  docker-logs    - View Docker logs"
	@echo "  docker-clean   - Clean up Docker resources"
	@echo ""
	@echo "🧹 Utilities:"
	@echo "  clean          - Clean up temporary files"
	@echo "  test           - Run comprehensive API test suite"
	@echo "  dev-setup      - Setup development environment (same as docker-start)"
	@echo ""

# Docker commands (Primary method)
docker-start:
	@echo "🐳 Starting Weather Chat API with Docker..."
	@echo "⚠️  You will be prompted for your OpenAI API key (not stored)"
	python start_docker.py

docker-build:
	@echo "🐳 Building Docker images..."
	docker compose build --no-cache

docker-up:
	@echo "🐳 Starting with Docker Compose..."
	docker compose up -d
	@echo "✅ Services started. Check logs with: make docker-logs"

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker compose down

docker-logs:
	@echo "📋 Docker logs:"
	docker compose logs -f

docker-clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker compose down -v
	docker system prune -f

# Run comprehensive test suite (requires running API)
test:
	@echo "🧪 Running comprehensive API test suite..."
	@./test_api.sh

# Clean up temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Development setup (alias for docker-start)
dev-setup:
	@echo "🛠️ Setting up development environment..."
	$(MAKE) docker-start 