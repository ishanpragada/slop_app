import redis
import os
from typing import Optional, List, Dict, Any
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RedisService:
    """Service for Redis operations and connection management"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection"""
        try:
            # Get Redis configuration from environment variables
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {redis_host}:{redis_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except Exception:
            pass
        return False
    
    def reconnect(self):
        """Attempt to reconnect to Redis"""
        self._connect()
    
    def get_client(self) -> redis.Redis:
        """Get the Redis client, reconnecting if necessary"""
        if not self.is_connected():
            self.reconnect()
        
        if not self.redis_client:
            raise Exception("Redis connection is not available")
        
        return self.redis_client
    
    # Feed-specific methods
    def add_to_feed(self, user_id: str, video_id: str, score: float = 0.0) -> bool:
        """Add a video to a user's feed with a score"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.zadd(feed_key, {video_id: score})
            return result > 0
        except Exception as e:
            logger.error(f"Failed to add video {video_id} to feed for user {user_id}: {str(e)}")
            return False
    
    def get_feed_videos(self, user_id: str, start: int = 0, count: int = 10, reverse: bool = True) -> List[str]:
        """Get videos from a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            
            if reverse:
                # Get highest scores first (best videos)
                videos = client.zrevrange(feed_key, start, start + count - 1)
            else:
                videos = client.zrange(feed_key, start, start + count - 1)
            
            return list(videos)
        except Exception as e:
            logger.error(f"Failed to get feed videos for user {user_id}: {str(e)}")
            return []
    
    def remove_from_feed(self, user_id: str, video_id: str) -> bool:
        """Remove a video from a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.zrem(feed_key, video_id)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to remove video {video_id} from feed for user {user_id}: {str(e)}")
            return False
    
    def get_feed_size(self, user_id: str) -> int:
        """Get the number of videos in a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            return client.zcard(feed_key)
        except Exception as e:
            logger.error(f"Failed to get feed size for user {user_id}: {str(e)}")
            return 0
    
    def clear_feed(self, user_id: str) -> bool:
        """Clear all videos from a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.delete(feed_key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to clear feed for user {user_id}: {str(e)}")
            return False
    
    def set_feed_expiry(self, user_id: str, seconds: int = 3600) -> bool:
        """Set expiry time for a user's feed (default 1 hour)"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.expire(feed_key, seconds)
            return result
        except Exception as e:
            logger.error(f"Failed to set expiry for feed {user_id}: {str(e)}")
            return False 