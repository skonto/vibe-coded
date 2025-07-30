import json
import redis.asyncio as redis
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.config import settings
from app.schemas.chat import ChatMessage, SessionInfo, SessionHistory, MessageRole
from app.utils.errors import SessionNotFoundException


class SessionService:
    """Service for managing user sessions and chat history."""
    
    def __init__(self):
        self.redis_client = None
    
    async def init_redis(self):
        """Initialize Redis connection."""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.redis_url)
    
    async def close_redis(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"session:{session_id}"
    
    def _history_key(self, session_id: str) -> str:
        """Generate Redis key for chat history."""
        return f"history:{session_id}"
    
    async def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session."""
        await self.init_redis()
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_info = SessionInfo(
            session_id=session_id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0
        )
        
        await self.redis_client.setex(
            self._session_key(session_id),
            settings.session_timeout,
            session_info.model_dump_json()
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> SessionInfo:
        """Get session information."""
        await self.init_redis()
        
        session_data = await self.redis_client.get(self._session_key(session_id))
        if not session_data:
            raise SessionNotFoundException(f"Session {session_id} not found")
        
        return SessionInfo.model_validate_json(session_data)
    
    async def update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp."""
        await self.init_redis()
        
        try:
            session_info = await self.get_session(session_id)
            session_info.last_activity = datetime.utcnow()
            session_info.message_count += 1
            
            await self.redis_client.setex(
                self._session_key(session_id),
                settings.session_timeout,
                session_info.model_dump_json()
            )
        except SessionNotFoundException:
            # Create new session if it doesn't exist
            await self.create_session(session_id)
    
    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Add message to chat history."""
        await self.init_redis()
        
        # Get current history
        messages = await self.get_chat_history(session_id)
        messages.append(message)
        
        # Limit history length
        if len(messages) > settings.max_history_length:
            messages = messages[-settings.max_history_length:]
        
        # Store updated history
        messages_json = json.dumps([msg.model_dump() for msg in messages], default=str)
        await self.redis_client.setex(
            self._history_key(session_id),
            settings.session_timeout,
            messages_json
        )
        
        # Update session activity
        await self.update_session_activity(session_id)
    
    async def get_chat_history(self, session_id: str) -> List[ChatMessage]:
        """Get chat history for session."""
        await self.init_redis()
        
        history_data = await self.redis_client.get(self._history_key(session_id))
        if not history_data:
            return []
        
        messages_data = json.loads(history_data)
        return [ChatMessage.model_validate(msg) for msg in messages_data]
    
    async def get_session_history(self, session_id: str) -> SessionHistory:
        """Get complete session history."""
        session_info = await self.get_session(session_id)
        messages = await self.get_chat_history(session_id)
        
        return SessionHistory(
            session_id=session_id,
            messages=messages,
            session_info=session_info
        )
    
    async def update_user_preferences(
        self, 
        session_id: str, 
        preferred_city: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update user preferences for session."""
        await self.init_redis()
        
        try:
            session_info = await self.get_session(session_id)
            
            if preferred_city:
                session_info.preferred_city = preferred_city
            
            if preferences:
                session_info.preferences.update(preferences)
            
            await self.redis_client.setex(
                self._session_key(session_id),
                settings.session_timeout,
                session_info.model_dump_json()
            )
        except SessionNotFoundException:
            # Create new session with preferences
            session_id = await self.create_session(session_id)
            if preferred_city or preferences:
                await self.update_user_preferences(session_id, preferred_city, preferences)
    
    async def extract_city_preference(self, messages: List[ChatMessage]) -> Optional[str]:
        """Extract city preference from chat history."""
        # Simple heuristic to find the most recent city mentioned
        cities_mentioned = []
        
        for message in reversed(messages):
            if message.role == MessageRole.USER:
                content = message.content.lower()
                # Look for patterns like "weather in [city]", "how's [city]", etc.
                # This is a simple implementation - could be enhanced with NLP
                words = content.split()
                for i, word in enumerate(words):
                    if word in ["in", "at", "for"] and i + 1 < len(words):
                        potential_city = words[i + 1].strip(".,!?").title()
                        if len(potential_city) > 2:  # Basic validation
                            cities_mentioned.append(potential_city)
        
        return cities_mentioned[0] if cities_mentioned else None
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (useful for background tasks)."""
        await self.init_redis()
        
        # Redis handles TTL automatically, but we can implement additional cleanup logic here
        # For now, just return 0 as Redis handles expiration
        return 0


# Global session service instance
session_service = SessionService() 