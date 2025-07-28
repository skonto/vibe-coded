import asyncio
import json
import random
import string
import logging
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MCP_SERVER - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Simple MCP server implementation without stdio
class SimpleMCPServer:
    def __init__(self):
        logger.info("🚀 Initializing SimpleMCPServer...")
        self.tools = [
            {
                "name": "calculator",
                "description": "Perform basic arithmetic operations (add, subtract, multiply, divide)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The arithmetic operation to perform"
                        },
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            },
            {
                "name": "text_processor",
                "description": "Process text with various operations (uppercase, lowercase, reverse, count_words)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["uppercase", "lowercase", "reverse", "count_words"],
                            "description": "The text processing operation"
                        },
                        "text": {
                            "type": "string",
                            "description": "The text to process"
                        }
                    },
                    "required": ["operation", "text"]
                }
            },
            {
                "name": "data_analyzer",
                "description": "Analyze a list of numbers (sum, average, min, max)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["sum", "average", "min", "max"],
                            "description": "The analysis operation"
                        },
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of numbers to analyze"
                        }
                    },
                    "required": ["operation", "numbers"]
                }
            },
            {
                "name": "string_generator",
                "description": "Generate various types of strings (random, pattern, repeat)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["random", "pattern", "repeat"],
                            "description": "The string generation operation"
                        },
                        "length": {
                            "type": "integer",
                            "description": "Length of the string to generate"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Pattern for string generation (for pattern operation)"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to repeat (for repeat operation)"
                        }
                    },
                    "required": ["operation", "length"]
                }
            }
        ]
        logger.info(f"✅ MCP Server initialized with {len(self.tools)} tools: {[tool['name'] for tool in self.tools]}")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        logger.info("📋 Tool list requested")
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool and return the result."""
        logger.info(f"🛠️ Tool call requested: {name} with arguments: {arguments}")
        
        if name == "calculator":
            result = await self.calculator_tool(arguments)
        elif name == "text_processor":
            result = await self.text_processor_tool(arguments)
        elif name == "data_analyzer":
            result = await self.data_analyzer_tool(arguments)
        elif name == "string_generator":
            result = await self.string_generator_tool(arguments)
        else:
            logger.error(f"❌ Unknown tool requested: {name}")
            result = {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True
            }
        
        logger.info(f"✅ Tool {name} completed: {result}")
        return result
    
    async def calculator_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic arithmetic operations."""
        logger.info(f"🧮 Calculator tool called with args: {args}")
        operation = args.get("operation")
        a = args.get("a")
        b = args.get("b")
        
        try:
            if operation == "add":
                result = a + b
                logger.info(f"🧮 Addition: {a} + {b} = {result}")
            elif operation == "subtract":
                result = a - b
                logger.info(f"🧮 Subtraction: {a} - {b} = {result}")
            elif operation == "multiply":
                result = a * b
                logger.info(f"🧮 Multiplication: {a} * {b} = {result}")
            elif operation == "divide":
                if b == 0:
                    logger.error("❌ Division by zero attempted")
                    return {
                        "content": [{"type": "text", "text": "Error: Division by zero"}],
                        "isError": True
                    }
                result = a / b
                logger.info(f"🧮 Division: {a} / {b} = {result}")
            else:
                logger.error(f"❌ Unknown calculator operation: {operation}")
                return {
                    "content": [{"type": "text", "text": f"Unknown operation: {operation}"}],
                    "isError": True
                }
            
            return {
                "content": [{"type": "text", "text": f"Result: {result}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"❌ Calculator error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def text_processor_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process text with various operations."""
        logger.info(f"📝 Text processor tool called with args: {args}")
        operation = args.get("operation")
        text = args.get("text", "")
        
        try:
            if operation == "uppercase":
                result = text.upper()
                logger.info(f"📝 Uppercase: '{text}' -> '{result}'")
            elif operation == "lowercase":
                result = text.lower()
                logger.info(f"📝 Lowercase: '{text}' -> '{result}'")
            elif operation == "reverse":
                result = text[::-1]
                logger.info(f"📝 Reverse: '{text}' -> '{result}'")
            elif operation == "count_words":
                result = len(text.split())
                logger.info(f"📝 Word count: '{text}' -> {result} words")
            else:
                logger.error(f"❌ Unknown text operation: {operation}")
                return {
                    "content": [{"type": "text", "text": f"Unknown operation: {operation}"}],
                    "isError": True
                }
            
            return {
                "content": [{"type": "text", "text": f"Result: {result}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"❌ Text processor error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def data_analyzer_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a list of numbers."""
        logger.info(f"📊 Data analyzer tool called with args: {args}")
        operation = args.get("operation")
        numbers = args.get("numbers", [])
        
        try:
            if not numbers:
                logger.error("❌ No numbers provided for analysis")
                return {
                    "content": [{"type": "text", "text": "Error: No numbers provided"}],
                    "isError": True
                }
            
            if operation == "sum":
                result = sum(numbers)
                logger.info(f"📊 Sum: {numbers} -> {result}")
            elif operation == "average":
                result = sum(numbers) / len(numbers)
                logger.info(f"📊 Average: {numbers} -> {result}")
            elif operation == "min":
                result = min(numbers)
                logger.info(f"📊 Min: {numbers} -> {result}")
            elif operation == "max":
                result = max(numbers)
                logger.info(f"📊 Max: {numbers} -> {result}")
            else:
                logger.error(f"❌ Unknown data analysis operation: {operation}")
                return {
                    "content": [{"type": "text", "text": f"Unknown operation: {operation}"}],
                    "isError": True
                }
            
            return {
                "content": [{"type": "text", "text": f"Result: {result}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"❌ Data analyzer error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def string_generator_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate various types of strings."""
        logger.info(f"🔤 String generator tool called with args: {args}")
        operation = args.get("operation")
        length = args.get("length", 10)
        
        try:
            if operation == "random":
                result = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
                logger.info(f"🔤 Random string (length {length}): '{result}'")
            elif operation == "pattern":
                pattern = args.get("pattern", "abc")
                result = (pattern * (length // len(pattern) + 1))[:length]
                logger.info(f"🔤 Pattern string (length {length}, pattern '{pattern}'): '{result}'")
            elif operation == "repeat":
                text = args.get("text", "x")
                result = (text * (length // len(text) + 1))[:length]
                logger.info(f"🔤 Repeat string (length {length}, text '{text}'): '{result}'")
            else:
                logger.error(f"❌ Unknown string generation operation: {operation}")
                return {
                    "content": [{"type": "text", "text": f"Unknown operation: {operation}"}],
                    "isError": True
                }
            
            return {
                "content": [{"type": "text", "text": f"Generated string: {result}"}],
                "isError": False
            }
        except Exception as e:
            logger.error(f"❌ String generator error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }

# Global server instance
mcp_server = SimpleMCPServer()

# For backward compatibility with the original MCP interface
async def main():
    """Main function for standalone MCP server."""
    print("MCP Server initialized with tools:")
    for tool in mcp_server.tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Keep the server running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main()) 