from openai import OpenAI
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
import re

from app.core.config import settings
from app.schemas.chat import ChatMessage, MessageRole, ChatResponse, WeatherData
from app.services.session_service import session_service
from app.utils.errors import OpenAIException
import subprocess
import json
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ChatService:
    """Service for handling chat conversations with OpenAI integration."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    def _create_system_prompt(self, session_history: List[ChatMessage], preferred_city: Optional[str] = None) -> str:
        """Create system prompt based on user preferences and context."""
        base_prompt = """You are a helpful weather assistant that provides weather information for cities around the world. 
You have access to current weather data from Open-Meteo (a free, accurate weather service) and can search the web for additional information when needed.

Key guidelines:
1. Always be friendly and conversational
2. Provide accurate weather information when requested
3. Remember user preferences for cities they frequently ask about
4. If a user asks about weather without specifying a city, use their preferred city if known
5. Provide context about weather conditions (what to wear, activities, etc.)
6. Use the available tools to get current weather data and web search when needed
7. Keep responses concise but informative
8. The weather data comes from Open-Meteo, which provides high-quality forecasts from national weather services
9. If you need to search for weather-related information not available in the weather API, use web search"""
        
        # Add user context if available
        if preferred_city:
            base_prompt += f"\n\nUser's preferred city: {preferred_city}"
        
        # Add conversation context
        if session_history:
            recent_cities = self._extract_cities_from_history(session_history)
            if recent_cities:
                base_prompt += f"\n\nCities recently discussed: {', '.join(recent_cities[:3])}"
        
        return base_prompt
    
    def _extract_cities_from_history(self, messages: List[ChatMessage]) -> List[str]:
        """Extract city names from conversation history."""
        cities = []
        city_patterns = [
            r'weather (?:in|at|for) (\w+)',
            r'how.*(?:in|at) (\w+)',
            r'temperature (?:in|at|for) (\w+)',
            r'forecast (?:in|at|for) (\w+)'
        ]
        
        for message in messages[-10:]:  # Look at last 10 messages
            if message.role == MessageRole.USER:
                content = message.content.lower()
                for pattern in city_patterns:
                    matches = re.findall(pattern, content)
                    cities.extend([city.title() for city in matches])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(cities))
    
    def _should_get_weather(self, user_message: str) -> Optional[str]:
        """Determine if weather data should be fetched and for which city."""
        message_lower = user_message.lower()
        
        # Weather-related keywords
        weather_keywords = [
            'weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast',
            'hot', 'cold', 'warm', 'cool', 'humidity', 'wind', 'snow'
        ]
        
        if not any(keyword in message_lower for keyword in weather_keywords):
            return None
        
        # Extract city from message
        city_patterns = [
            r'(?:in|at|for) (\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*) weather',
            r'weather (\w+(?:\s+\w+)*)',
        ]
        
        for pattern in city_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                # Clean up the match
                city = matches[0].strip().title()
                if len(city) > 2 and city not in ['In', 'At', 'For', 'The']:
                    return city
        
        return "unknown"  # Weather-related but no city specified
    
    async def _get_mcp_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of tools from MCP server."""
        tools = []
        
        # Use the mcp_server.py file directly via stdio
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    tools_result = await session.list_tools()
                    
                    for tool in tools_result.tools:
                        tools.append({
                            "name": tool.name,
                            "description": tool.description or "",
                            "inputSchema": tool.inputSchema or {}
                        })
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}")
        
        return tools
    
    async def _get_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format."""
        tools = await self._get_mcp_tools_list()
        
        openai_tools = []
        for tool in tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def _execute_function_calls(self, function_calls: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], Optional[WeatherData]]:
        """Execute function calls using MCP client."""
        function_results = []
        tools_used = []
        weather_data = None
        
        # Use the mcp_server.py file directly via stdio
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    for func_call in function_calls:
                        tool_name = func_call["name"]
                        try:
                            parameters = json.loads(func_call["arguments"])
                        except json.JSONDecodeError:
                            parameters = {}
                        
                        try:
                            # Call tool via MCP client
                            result = await session.call_tool(tool_name, arguments=parameters)
                            
                            # Extract content from result
                            content_text = ""
                            if result.content:
                                for content_item in result.content:
                                    if hasattr(content_item, 'text'):
                                        content_text += content_item.text
                                    elif hasattr(content_item, 'type') and content_item.type == "text":
                                        content_text += str(content_item)
                            
                            # Check for structured content (from Pydantic models)
                            if hasattr(result, 'structuredContent') and result.structuredContent:
                                structured_data = result.structuredContent
                                
                                # For weather tools, try to extract weather data
                                if tool_name in ["get_weather", "get_weather_forecast"]:
                                    try:
                                        if isinstance(structured_data, dict) and "temperature" in structured_data:
                                            weather_data = WeatherData(**structured_data)
                                    except Exception:
                                        pass
                                
                                # Use structured content if available, otherwise use text
                                if not content_text:
                                    content_text = json.dumps(structured_data, indent=2)
                            
                            function_results.append({
                                "role": "function",
                                "name": tool_name,
                                "content": content_text
                            })
                            
                            tools_used.append(tool_name)
                            
                        except Exception as e:
                            logger.error(f"Error calling tool {tool_name}: {e}")
                            function_results.append({
                                "role": "function",
                                "name": tool_name,
                                "content": f"Error executing {tool_name}: {str(e)}"
                            })
                
        except Exception as e:
            logger.error(f"Error setting up MCP session: {e}")
            for func_call in function_calls:
                function_results.append({
                    "role": "function",
                    "name": func_call["name"],
                    "content": f"Error: Could not connect to MCP server: {str(e)}"
                })
        
        return function_results, tools_used, weather_data
    
    def _format_conversation_for_openai(
        self, 
        messages: List[ChatMessage], 
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """Format conversation history for OpenAI API."""
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to recent messages)
        recent_messages = messages[-20:] if len(messages) > 20 else messages
        
        for message in recent_messages:
            openai_messages.append({
                "role": message.role.value,
                "content": message.content
            })
        
        return openai_messages
    
    async def generate_response(
        self, 
        session_id: str, 
        user_message: str,
        city_hint: Optional[str] = None
    ) -> ChatResponse:
        """Generate response using OpenAI with context and tools."""
        try:
            # Get session history and preferences
            history = await session_service.get_chat_history(session_id)
            
            try:
                session_info = await session_service.get_session(session_id)
                preferred_city = session_info.preferred_city
            except:
                preferred_city = None
            
            # Update preferred city if city_hint is provided
            if city_hint and not preferred_city:
                await session_service.update_user_preferences(session_id, preferred_city=city_hint)
                preferred_city = city_hint
            
            # Add user message to history
            user_chat_message = ChatMessage(
                role=MessageRole.USER,
                content=user_message,
                timestamp=datetime.utcnow()
            )
            await session_service.add_message(session_id, user_chat_message)
            history.append(user_chat_message)
            
            # Initialize variables (will be set by function calling if needed)
            weather_data = None
            tools_used = []
            
            # Extract potential city preference from conversation
            if not preferred_city:
                inferred_city = await session_service.extract_city_preference(history)
                if inferred_city:
                    await session_service.update_user_preferences(session_id, preferred_city=inferred_city)
                    preferred_city = inferred_city
            
            # Create system prompt with context
            system_prompt = self._create_system_prompt(history, preferred_city)
            
            # Format messages for OpenAI (without weather data initially)
            openai_messages = self._format_conversation_for_openai(
                history[:-1],  # Exclude the user message we just added
                system_prompt
            )
            
            # Add the current user message
            openai_messages.append({"role": "user", "content": user_message})
            
            # Get available tools for function calling
            available_tools = await self._get_openai_tools()
            
            # Call OpenAI API with function calling
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=openai_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    tools=available_tools if available_tools else None,
                    tool_choice="auto" if available_tools else None,
                    timeout=30.0
                )
                
                message = response.choices[0].message
                assistant_response = message.content or ""
                
                # Handle function calls if present
                function_results = []
                if message.tool_calls:
                    function_calls = [
                        {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                            "id": call.id
                        }
                        for call in message.tool_calls
                    ]
                    
                    function_results, tools_used, weather_data = await self._execute_function_calls(function_calls)
                    
                    # Add function results to conversation and get final response
                    if function_results:
                        # Add assistant message with tool calls (use original message data)
                        openai_messages.append({
                            "role": "assistant", 
                            "content": assistant_response,
                            "tool_calls": [
                                {
                                    "id": call.id,
                                    "type": "function",
                                    "function": {"name": call.function.name, "arguments": call.function.arguments}
                                }
                                for call in message.tool_calls
                            ]
                        })
                        
                        # Add function results with matching IDs
                        for i, result in enumerate(function_results):
                            openai_messages.append({
                                "role": "tool",
                                "content": result["content"],
                                "tool_call_id": function_calls[i]["id"]
                            })
                        
                        # Get final response with function results
                        final_response = self.client.chat.completions.create(
                            model=self.model,
                            messages=openai_messages,
                            max_tokens=self.max_tokens,
                            temperature=self.temperature,
                            timeout=30.0
                        )
                        
                        assistant_response = final_response.choices[0].message.content or assistant_response
                
            except Exception as e:
                error_message = str(e)
                if "rate_limit" in error_message.lower():
                    raise OpenAIException("Rate limit exceeded. Please try again later.")
                elif "authentication" in error_message.lower() or "api_key" in error_message.lower():
                    raise OpenAIException("OpenAI authentication failed. Please check API key.")
                elif "api" in error_message.lower():
                    raise OpenAIException(f"OpenAI API error: {error_message}")
                else:
                    raise OpenAIException(f"Unexpected OpenAI error: {error_message}")
            
            # Add assistant response to history
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=assistant_response,
                timestamp=datetime.utcnow()
            )
            await session_service.add_message(session_id, assistant_message)
            
            # Prepare response
            response_data = {
                "session_id": session_id,
                "response": assistant_response,
                "timestamp": datetime.utcnow()
            }
            
            if weather_data:
                response_data["weather_data"] = weather_data.model_dump()
            
            if tools_used:
                response_data["tools_used"] = tools_used
            
            return ChatResponse(**response_data)
            
        except OpenAIException:
            raise
        except Exception as e:
            raise OpenAIException(f"Unexpected error in chat service: {str(e)}")
    
    async def get_conversation_summary(self, session_id: str) -> str:
        """Generate a summary of the conversation for context."""
        try:
            history = await session_service.get_chat_history(session_id)
            
            if not history:
                return "No conversation history available."
            
            # Create a simple summary
            user_messages = [msg for msg in history if msg.role == MessageRole.USER]
            cities_discussed = self._extract_cities_from_history(history)
            
            summary = f"Conversation with {len(user_messages)} user messages."
            if cities_discussed:
                summary += f" Cities discussed: {', '.join(cities_discussed[:5])}"
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"


# Global chat service instance
chat_service = ChatService() 