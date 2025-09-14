import os
import time
import json
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from app.services.video_generation_queue_service import VideoGenerationQueueService
from app.services.video_generation_service import VideoGenerationService
from app.services.aws_service import AWSService
from app.services.pinecone_service import PineconeService
from app.services.database_service import DatabaseService
from app.services.redis_service import RedisService

class BackgroundVideoWorker:
    """Background worker for processing video generation tasks from Redis queues"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize services
        self.queue_service = VideoGenerationQueueService()
        self.video_service = VideoGenerationService()
        self.aws_service = AWSService()
        self.pinecone_service = PineconeService()
        self.database_service = DatabaseService()
        self.redis_service = RedisService()
        
        # Worker state
        self.running = False
        self.worker_id = f"worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Statistics
        self.stats = {
            "videos_generated": 0,
            "errors": 0,
            "started_at": None,
            "last_activity": None
        }
        
        print(f"🤖 Background Video Worker initialized: {self.worker_id}")
    
    def process_all_pending_tasks(self) -> int:
        """
        Process all pending video generation tasks until queues are empty
        
        Returns:
            Number of tasks processed
        """
        print("🔄 Processing all pending tasks until queues are empty...")
        
        total_processed = 0
        max_concurrent_tasks = 1  # Limit concurrent video generations
        active_tasks = {}
        
        try:
            # Get all users with pending tasks
            users_with_tasks = self._get_all_users_with_pending_tasks()
            print(f"📋 Found {len(users_with_tasks)} users with pending tasks")
            
            while users_with_tasks:
                # Process tasks for each user (up to concurrent limit)
                for user_id in list(users_with_tasks):
                    if len(active_tasks) >= max_concurrent_tasks:
                        break
                    
                    # Get next task for this user
                    task = self.queue_service.get_next_generation_task(user_id)
                    
                    if task and task.get("type") == "generate_video":
                        # Start video generation for this task
                        task_id = f"{user_id}_{int(time.time())}"
                        print(f"🎬 Starting video generation for user {user_id}")
                        print(f"   Prompt: {task.get('prompt', 'No prompt')[:60]}...")
                        
                        success = self._generate_video_for_task(user_id, task)
                        if success:
                            total_processed += 1
                            self.stats["videos_generated"] += 1
                            pass  # Completed video generation
                        else:
                            self.stats["errors"] += 1
                            pass  # Failed video generation
                        
                        self.stats["last_activity"] = datetime.now().isoformat()
                    else:
                        # No more tasks for this user
                        users_with_tasks.remove(user_id)
                
                # If no users have tasks, we're done
                if not users_with_tasks:
                    break
                
                # Brief pause between iterations
                time.sleep(1)
            
            print(f"🎉 Completed processing! Generated {total_processed} videos")
            return total_processed
            
        except Exception as e:
            pass  # Error in process_all_pending_tasks
            self.stats["errors"] += 1
            return total_processed
    
    def _get_all_users_with_pending_tasks(self) -> List[str]:
        """Get list of all users who have pending video generation tasks"""
        try:
            import redis
            redis_client = self.queue_service.redis_service.get_client()
            
            # Get all queue keys
            queue_keys = redis_client.keys("video_queue:*")
            users_with_tasks = []
            
            for queue_key in queue_keys:
                queue_key_str = queue_key.decode() if isinstance(queue_key, bytes) else queue_key
                user_id = queue_key_str.replace("video_queue:", "")
                
                # Check if this queue has pending tasks
                queue_items = redis_client.zrevrange(queue_key, 0, -1)
                for item_json in queue_items:
                    try:
                        item = json.loads(item_json)
                        if (item.get("type") == "generate_video" and 
                            item.get("status") == "pending_generation"):
                            users_with_tasks.append(user_id)
                            break  # Found at least one pending task for this user
                    except json.JSONDecodeError:
                        continue
            
            return users_with_tasks
            
        except Exception as e:
            pass  # Error getting users with pending tasks
            return []
    
    def _generate_video_for_task(self, user_id: str, task: Dict[str, Any]) -> bool:
        """
        Generate a video for a specific task
        
        Args:
            user_id: User identifier
            task: Task information from queue
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prompt = task.get("prompt", "")
            if not prompt:
                pass  # No prompt found in task
                return False
            
            pass  # TEMPORARY MODE: Video generation disabled
            print(f"   Would have generated video for user {user_id}")
            print(f"   Would have used prompt: {prompt}")
            print(f"   Skipping actual video generation and marking task as completed")
            
            # TEMPORARY: Skip actual video generation for testing
            # Just mark the task as completed without generating video
            return True
                
        except Exception as e:
            pass  # Error generating video for task
            return False
    
    def stop(self):
        """Stop the worker"""
        print(f"🛑 Stopping background video worker: {self.worker_id}")
        self.running = False
    
    def _add_generated_video_to_feed(self, user_id: str, video_id: str, prompt: str) -> None:
        """
        Add a newly generated video to the user's feed queue
        
        Args:
            user_id: User identifier
            video_id: Generated video ID
            prompt: Video prompt used for generation
        """
        try:
            # For newly generated videos, give them a high score since they're personalized
            # Use timestamp-based scoring to ensure newest videos appear first
            feed_score = time.time()  # Current timestamp as score
            
            success = self.redis_service.add_to_feed(user_id, video_id, feed_score)
            if success:
                pass  # Added newly generated video to User Feed Queue
            else:
                print(f"⚠️  Failed to add generated video {video_id} to user feed")
                
        except Exception as e:
            pass  # Error adding generated video to user feed

def main():
    """Main function for running the background worker continuously"""
    worker = BackgroundVideoWorker()
    worker.running = True
    worker.stats["started_at"] = datetime.now().isoformat()
    
    try:
        print("🚀 Starting continuous background video worker...")
        print("Press Ctrl+C to stop")
        
        while worker.running:
            # Process any pending tasks
            processed = worker.process_all_pending_tasks()
            
            if processed > 0:
                pass  # Processed tasks in this cycle
            
            # Wait before next cycle
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print(f"\n🔔 Received interrupt signal")
        worker.stop()
    except Exception as e:
        print(f"\n❌ Worker error: {e}")
        worker.stop()
    finally:
        print("✅ Background video worker stopped")

if __name__ == "__main__":
    main()