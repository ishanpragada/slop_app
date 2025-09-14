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
            
            # Reset any stuck tasks before processing
            for user_id in users_with_tasks:
                reset_count = self.queue_service.reset_stuck_tasks(user_id)
                if reset_count > 0:
                    print(f"🔄 Reset {reset_count} stuck tasks for user {user_id}")
            
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
                            print(f"✅ Successfully completed video generation for user {user_id}")
                        else:
                            self.stats["errors"] += 1
                            print(f"❌ Failed video generation for user {user_id}")
                            # Mark task as failed so it doesn't get stuck in_progress
                            self._mark_task_failed(user_id, task)
                        
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
            print(f"❌ Error in process_all_pending_tasks: {e}")
            print(f"   Exception type: {type(e).__name__}")
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
            
            print(f"🎬 Generating video for user {user_id}")
            print(f"📝 Prompt: {prompt}")
            
            # Import video generation service here to avoid circular imports
            from app.services.video_generation_service import VideoGenerationService
            from app.services.aws_service import AWSService
            from app.services.pinecone_service import PineconeService
            
            # Initialize services
            video_service = VideoGenerationService()
            aws_service = AWSService()
            pinecone_service = PineconeService()
            
            # Generate video with S3 upload enabled
            result = video_service.generate_video_complete(
                prompt=prompt,
                upload_to_s3=True,
                aws_service=aws_service,
                pinecone_service=pinecone_service
            )
            
            if result.generation_complete and result.s3_url:
                print(f"✅ Video generation completed successfully")
                print(f"   🎬 Video ID: {result.video_id}")
                print(f"   🔗 S3 URL: {result.s3_url}")
                
                # Save video metadata to PostgreSQL database
                self._save_video_to_database(result.video_id, result.s3_url, prompt)
                
                # Add the generated video to user's feed
                self._add_generated_video_to_feed(user_id, result.video_id, prompt)
                
                # Mark the task as completed and remove from generation queue
                completion_success = self.queue_service.mark_generation_complete(
                    user_id, task, result.video_id, result.s3_url
                )
                
                if completion_success:
                    print(f"✅ Marked generation task as completed for user {user_id}")
                else:
                    print(f"⚠️  Failed to mark task as completed for user {user_id}")
                
                return True
            else:
                print(f"❌ Video generation failed or incomplete")
                return False
                
        except Exception as e:
            print(f"❌ Error generating video for task: {e}")
            print(f"   Exception type: {type(e).__name__}")
            print(f"   User: {user_id}")
            print(f"   Prompt: {prompt}")
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
            # For newly generated videos, give them a high but reasonable score
            # Generated videos are highly personalized, so give them similarity of ~0.9 + freshness boost
            # This ensures they rank high but don't completely dominate the feed
            base_personalization_score = 0.9  # High similarity since generated for this user
            freshness_boost = 0.1  # Small boost for being newly generated
            feed_score = base_personalization_score + freshness_boost
            
            success = self.redis_service.add_to_feed(user_id, video_id, feed_score)
            if success:
                print(f"✅ Added newly generated video {video_id} to user feed (score: {feed_score})")
            else:
                print(f"⚠️  Failed to add generated video {video_id} to user feed")
                
        except Exception as e:
            print(f"❌ Error adding generated video to user feed: {e}")
            print(f"   Video ID: {video_id}")
            print(f"   User ID: {user_id}")
            print(f"   Score: {feed_score if 'feed_score' in locals() else 'N/A'}")
    
    def _save_video_to_database(self, video_id: str, s3_url: str, prompt: str) -> None:
        """
        Save generated video metadata to PostgreSQL database
        
        Args:
            video_id: Generated video ID
            s3_url: S3 URL of the video
            prompt: Text prompt used for generation
        """
        try:
            result = self.database_service.save_video_metadata(
                video_id=video_id,
                s3_url=s3_url,
                prompt=prompt,
                length_seconds=8  # Veo 3 Fast generates 8-second videos
            )
            
            if result.get("success"):
                print(f"✅ Saved video metadata to database: {video_id}")
                print(f"   📝 Prompt: {prompt}")
                print(f"   🔗 S3 URL: {s3_url}")
            else:
                print(f"❌ Failed to save video metadata to database: {result.get('message', 'unknown error')}")
                
        except Exception as e:
            print(f"❌ Error saving video to database: {e}")
            print(f"   Video ID: {video_id}")
            print(f"   Prompt: {prompt}")
    
    def _mark_task_failed(self, user_id: str, task: Dict[str, Any]) -> None:
        """
        Mark a task as failed to prevent it from being stuck in_progress
        
        Args:
            user_id: User identifier
            task: The failed task
        """
        try:
            queue_key = f"video_queue:{user_id}"
            client = self.redis_service.get_client()
            
            # Update task status to failed
            task["status"] = "failed"
            task["failed_at"] = datetime.now().isoformat()
            task["error"] = "Video generation failed"
            
            # Find and replace the task in queue
            queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            for item_json, score in queue_items:
                try:
                    item = json.loads(item_json)
                    
                    # Match by prompt and user_id
                    if (item.get("prompt") == task.get("prompt") and 
                        item.get("user_id") == task.get("user_id")):
                        
                        # Remove old task and add updated one
                        client.zrem(queue_key, item_json)
                        client.zadd(queue_key, {json.dumps(task): score})
                        
                        print(f"🚨 Marked task as failed for user {user_id}")
                        return
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"❌ Error marking task as failed: {e}")

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