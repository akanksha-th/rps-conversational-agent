import redis
import json
from typing import Optional, Any
from src.core.config import get_settings

settings = get_settings()


class CacheService:
    def __init__(self):
        self.redis_server = redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True
        )
        self.ttl = settings.CACHE_TTL

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from cache"""
        data = self.redis_server.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Store data in cache as JSON string"""
        expire = expire or self.ttl
        return self.redis_server.set(
            key, json.dumps(value),
            ex=expire
        )

    def delete(self, key: str) -> bool:
        """Remove a specific key from cache"""
        return bool(self.redis_server.delete(key))

    def flush_all(self):
        """Clear the entire cache"""
        return self.redis_server.flushdb()
    
    @staticmethod
    def generate_analysis_key(video_id: str, max_comments: int) -> str:
        """Generate consistent cache key for analysis results"""
        return f"analysis:{video_id}:{max_comments}"