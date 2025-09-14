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
            pass  # Successfully connected to Redis
            
        except Exception as e:
            pass  # Failed to connect to Redis
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
            
            # ZADD returns number of NEW elements added, 0 if element existed and was updated
            # We consider both cases as success
            # Only log for debugging when needed
            # print(f"🔍 Redis ZADD result for video {video_id}: {result} (0=updated existing, >0=new element)")
            return True  # Both new additions and score updates are successful
            
        except Exception as e:
            print(f"❌ Failed to add video to feed: {e}")
            print(f"   User ID: {user_id}")
            print(f"   Video ID: {video_id}")
            print(f"   Score: {score}")
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
            pass  # Failed to get feed videos
            return []
    
    def remove_from_feed(self, user_id: str, video_id: str) -> bool:
        """Remove a video from a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.zrem(feed_key, video_id)
            return result > 0
        except Exception as e:
            pass  # Failed to remove video from feed
            return False
    
    def get_feed_size(self, user_id: str) -> int:
        """Get the number of videos in a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            return client.zcard(feed_key)
        except Exception as e:
            pass  # Failed to get feed size
            return 0
    
    def clear_feed(self, user_id: str) -> bool:
        """Clear all videos from a user's feed"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.delete(feed_key)
            return result > 0
        except Exception as e:
            pass  # Failed to clear feed
            return False
    
    def set_feed_expiry(self, user_id: str, seconds: int = 3600) -> bool:
        """Set expiry time for a user's feed (default 1 hour)"""
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            result = client.expire(feed_key, seconds)
            return result
        except Exception as e:
            pass  # Failed to set expiry
    
    def display_next_reels(self, user_id: str, count: int = 5, start_position: int = 0) -> None:
        """
        Display the next reels in the user's feed queue with prompts
        
        Args:
            user_id: User identifier
            count: Number of reels to display (default: 5)
            start_position: Position to start from (default: 0)
        """
        try:
            client = self.get_client()
            feed_key = f"user:feed:{user_id}"
            
            # Get the next videos with scores starting from the specified position
            videos_with_scores = client.zrevrange(feed_key, start_position, start_position + count - 1, withscores=True)
            
            print(f"\n📺 Next {len(videos_with_scores)} reels in FEED QUEUE for user {user_id}:")
            print(f"🔑 Redis Key: {feed_key}")
            print(f"📍 Starting from position: {start_position}")
            print("=" * 80)
            
            if not videos_with_scores:
                print("📭 No reels in queue")
                return
            
            # Import DatabaseService here to avoid circular imports
            from app.services.database_service import DatabaseService
            database_service = DatabaseService()
            
            for i, (video_id, score) in enumerate(videos_with_scores):
                # Calculate the actual position in the queue
                actual_position = start_position + i + 1
                
                # Extract original video ID if it has infinite feed suffixes
                original_video_id = video_id.split(':')[0] if ':' in video_id else video_id
                
                # Get video metadata from database
                video_info = database_service.get_video_by_id(original_video_id)
                prompt = "N/A"
                if video_info and 'prompt' in video_info:
                    prompt = video_info['prompt']
                    # Truncate prompt if too long
                    if len(prompt) > 60:
                        prompt = prompt[:60] + "..."
                
                print(f"{actual_position}. ID: {video_id[:20]}... | Score: {score:.2f}")
                print(f"   📝 Prompt: {prompt}")
                if i < len(videos_with_scores) - 1:  # Don't add separator after last item
                    print("   " + "-" * 70)
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error displaying next reels: {str(e)}")
    
    def display_video_generation_queue(self, user_id: str, count: int = 5) -> None:
        """
        Display the next items in the user's video generation queue
        
        Args:
            user_id: User identifier
            count: Number of items to display (default: 5)
        """
        try:
            client = self.get_client()
            queue_key = f"video_queue:{user_id}"
            
            # Get the next items with scores
            items_with_scores = client.zrevrange(queue_key, 0, count - 1, withscores=True)
            
            print(f"\n🎬 Next {len(items_with_scores)} items in VIDEO GENERATION QUEUE for user {user_id}:")
            print(f"🔑 Redis Key: {queue_key}")
            print("=" * 80)
            
            if not items_with_scores:
                print("📭 No items in generation queue")
                return
            
            for i, (item_json, score) in enumerate(items_with_scores, 1):
                try:
                    # Parse the JSON item
                    import json
                    item = json.loads(item_json)
                    
                    item_type = item.get("type", "unknown")
                    video_id = item.get("video_id", "N/A")
                    prompt = item.get("prompt", "N/A")
                    status = item.get("status", "unknown")
                    
                    # Truncate prompt if too long
                    if len(prompt) > 60:
                        prompt = prompt[:60] + "..."
                    
                    print(f"{i}. Type: {item_type} | Status: {status} | Score: {score:.2f}")
                    print(f"   🆔 Video ID: {video_id[:30]}...")
                    print(f"   📝 Prompt: {prompt}")
                    if i < len(items_with_scores):  # Don't add separator after last item
                        print("   " + "-" * 70)
                        
                except json.JSONDecodeError:
                    print(f"{i}. [INVALID JSON] Score: {score:.2f}")
                    print(f"   Raw data: {item_json[:100]}...")
                    if i < len(items_with_scores):
                        print("   " + "-" * 70)
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error displaying video generation queue: {str(e)}")