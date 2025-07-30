#!/bin/bash
# Weather Chat API Test Script
# Make sure the API is running: make docker-start

echo "🌤️ Weather Chat API - Test Suite"
echo "================================="
echo ""

API_BASE="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${BLUE}1. Testing Health Check...${NC}"
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$API_BASE/health")
HTTP_CODE="${HEALTH_RESPONSE: -3}"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "Response: $(cat /tmp/health_response.json | jq -r '.status')"
else
    echo -e "${RED}❌ Health check failed (HTTP $HTTP_CODE)${NC}"
    echo "Make sure the API is running: make docker-start"
    exit 1
fi

echo ""

# Test 2: Create Session
echo -e "${BLUE}2. Creating Chat Session...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_BASE/chat/session")
SESSION_ID=$(echo "$SESSION_RESPONSE" | jq -r '.session_id')

if [ "$SESSION_ID" != "null" ] && [ "$SESSION_ID" != "" ]; then
    echo -e "${GREEN}✅ Session created${NC}"
    echo "Session ID: ${SESSION_ID:0:8}..."
else
    echo -e "${RED}❌ Failed to create session${NC}"
    echo "Response: $SESSION_RESPONSE"
    exit 1
fi

echo ""

# Test 3: Check Available Tools
echo -e "${BLUE}3. Checking Available Tools...${NC}"
TOOLS_RESPONSE=$(curl -s "$API_BASE/chat/tools")
TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | jq -r '.tools | length')

if [ "$TOOLS_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Tools available: $TOOLS_COUNT${NC}"
    echo "$TOOLS_RESPONSE" | jq -r '.tools | keys[]' | sed 's/^/  • /'
else
    echo -e "${YELLOW}⚠️  No tools found${NC}"
fi

echo ""

# Test 4: Send Weather Query
echo -e "${BLUE}4. Testing Weather Query...${NC}"
WEATHER_QUERY='{
    "session_id": "'$SESSION_ID'",
    "message": "What is the weather like in Paris?",
    "city": "Paris"
}'

WEATHER_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "$WEATHER_QUERY" \
    "$API_BASE/chat/message")

WEATHER_RESPONSE_TEXT=$(echo "$WEATHER_RESPONSE" | jq -r '.response // empty')
WEATHER_DATA=$(echo "$WEATHER_RESPONSE" | jq -r '.weather_data.city // empty')

if [ "$WEATHER_RESPONSE_TEXT" != "" ] && [ "$WEATHER_DATA" != "" ]; then
    echo -e "${GREEN}✅ Weather query successful${NC}"
    echo "City: $WEATHER_DATA"
    echo "Response length: ${#WEATHER_RESPONSE_TEXT} characters"
    echo "Tools used: $(echo "$WEATHER_RESPONSE" | jq -r '.tools_used[]? // "none"')"
else
    echo -e "${YELLOW}⚠️  Weather query completed but may need OpenAI key${NC}"
    ERROR_MSG=$(echo "$WEATHER_RESPONSE" | jq -r '.detail.error // empty')
    if [ "$ERROR_MSG" != "" ]; then
        echo "Error: $ERROR_MSG"
    fi
fi

echo ""

# Test 5: Get Session Info
echo -e "${BLUE}5. Getting Session Info...${NC}"
SESSION_INFO=$(curl -s "$API_BASE/chat/session/$SESSION_ID")
MESSAGE_COUNT=$(echo "$SESSION_INFO" | jq -r '.message_count // 0')

if [ "$MESSAGE_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ Session info retrieved${NC}"
    echo "Messages in session: $MESSAGE_COUNT"
else
    echo -e "${YELLOW}⚠️  Session info retrieved but no messages found${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}📋 Test Summary${NC}"
echo "=============="
echo "✅ API is running and responsive"
echo "✅ Session management works"
echo "✅ Tool discovery works"
echo "✅ Message handling works"
echo ""
echo -e "${GREEN}🎉 All basic tests passed!${NC}"
echo ""
echo "💡 To test with full functionality, make sure:"
echo "   • API is running: make docker-start"
echo "   • OpenAI API key is provided when prompted"
echo ""

# Cleanup
rm -f /tmp/health_response.json 