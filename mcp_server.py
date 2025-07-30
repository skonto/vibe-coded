#!/usr/bin/env python3
"""
Weather and Web Search MCP Server

This server provides weather information and web search capabilities
using the official Anthropic MCP Python SDK.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-mcp-server")

# Create the MCP server
mcp = FastMCP("Weather & Web Search Server")

class WeatherData(BaseModel):
    """Weather data structure."""
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage") 
    pressure: float = Field(description="Atmospheric pressure in hPa")
    wind_speed: float = Field(description="Wind speed in km/h")
    description: str = Field(description="Weather description")
    city: str = Field(description="City name")
    country: str = Field(description="Country name")

class WeatherForecast(BaseModel):
    """Weather forecast structure."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    max_temp: float = Field(description="Maximum temperature in Celsius")
    min_temp: float = Field(description="Minimum temperature in Celsius") 
    description: str = Field(description="Weather description")

class ForecastData(BaseModel):
    """Weather forecast data structure."""
    city: str = Field(description="City name")
    country: str = Field(description="Country name")
    forecasts: List[WeatherForecast] = Field(description="List of daily forecasts")

class SearchResult(BaseModel):
    """Web search result structure."""
    title: str = Field(description="Page title")
    url: str = Field(description="Page URL")
    snippet: str = Field(description="Page snippet/description")

async def geocode_city(city: str) -> Optional[Dict[str, Any]]:
    """Get coordinates for a city using Open-Meteo geocoding API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result["name"],
                    "country": result.get("country", ""),
                    "admin1": result.get("admin1", "")
                }
    except Exception as e:
        logger.error(f"Error geocoding city {city}: {e}")
    return None

def get_weather_description(weather_code: int) -> str:
    """Convert weather code to description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, "Unknown")

@mcp.tool()
async def get_weather(city: str) -> WeatherData:
    """Get current weather information for a city using Open-Meteo API."""
    logger.info(f"Getting weather for city: {city}")
    
    # Get coordinates for the city
    location = await geocode_city(city)
    if not location:
        raise ValueError(f"Could not find coordinates for city: {city}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": ["temperature_2m", "relative_humidity_2m", "pressure_msl", 
                               "wind_speed_10m", "weather_code"],
                    "timezone": "auto"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            current = data["current"]
            weather_code = current.get("weather_code", 0)
            
            return WeatherData(
                temperature=current["temperature_2m"],
                humidity=current["relative_humidity_2m"],
                pressure=current["pressure_msl"],
                wind_speed=current["wind_speed_10m"],
                description=get_weather_description(weather_code),
                city=location["name"],
                country=location["country"]
            )
            
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        raise ValueError(f"Failed to fetch weather data: {str(e)}")

@mcp.tool()
async def get_weather_forecast(city: str, days: int = 5) -> ForecastData:
    """Get weather forecast for a city using Open-Meteo API."""
    if days < 1 or days > 16:
        raise ValueError("Days must be between 1 and 16")
        
    logger.info(f"Getting {days}-day forecast for city: {city}")
    
    # Get coordinates for the city
    location = await geocode_city(city)
    if not location:
        raise ValueError(f"Could not find coordinates for city: {city}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
                    "timezone": "auto",
                    "forecast_days": days
                }
            )
            response.raise_for_status()
            data = response.json()
            
            daily = data["daily"]
            forecasts = []
            
            for i in range(len(daily["time"])):
                weather_code = daily["weather_code"][i]
                forecasts.append(WeatherForecast(
                    date=daily["time"][i],
                    max_temp=daily["temperature_2m_max"][i],
                    min_temp=daily["temperature_2m_min"][i],
                    description=get_weather_description(weather_code)
                ))
            
            return ForecastData(
                city=location["name"],
                country=location["country"],
                forecasts=forecasts
            )
            
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
        raise ValueError(f"Failed to fetch weather forecast: {str(e)}")

@mcp.tool()
async def web_search(query: str, max_results: int = 5) -> List[SearchResult]:
    """Search the web using DuckDuckGo."""
    if max_results < 1 or max_results > 10:
        raise ValueError("max_results must be between 1 and 10")
        
    logger.info(f"Searching web for: {query}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10.0
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Parse DuckDuckGo results
            for result_div in soup.find_all('div', class_='result__body')[:max_results]:
                title_link = result_div.find('a', class_='result__a')
                snippet_div = result_div.find('a', class_='result__snippet')
                
                if title_link and snippet_div:
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    snippet = snippet_div.get_text(strip=True)
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet
                        ))
            
            return results
            
    except Exception as e:
        logger.error(f"Error performing web search: {e}")
        raise ValueError(f"Failed to perform web search: {str(e)}")

@mcp.tool()
async def get_web_content(url: str, max_length: int = 2000) -> str:
    """Fetch and extract text content from a web page."""
    logger.info(f"Fetching content from: {url}")
    
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL provided")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10.0,
                follow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
    except Exception as e:
        logger.error(f"Error fetching web content: {e}")
        raise ValueError(f"Failed to fetch web content: {str(e)}")

# Add a resource for server information
@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about this MCP server."""
    return json.dumps({
        "name": "Weather & Web Search MCP Server",
        "version": "1.0.0",
        "description": "Provides weather information and web search capabilities",
        "tools": [
            "get_weather - Get current weather for a city",
            "get_weather_forecast - Get weather forecast for a city", 
            "web_search - Search the web using DuckDuckGo",
            "get_web_content - Extract text content from web pages"
        ],
        "data_sources": [
            "Open-Meteo API (weather data)",
            "DuckDuckGo (web search)",
            "Web scraping (content extraction)"
        ]
    }, indent=2)

def main():
    """Run the MCP server."""
    logger.info("Starting Weather & Web Search MCP Server...")
    mcp.run()

if __name__ == "__main__":
    main() 