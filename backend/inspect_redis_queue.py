#!/usr/bin/env python3
"""
Script to inspect all video generation queues in Redis
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.redis_service import RedisService

def inspect_all_video_queues():
    """Inspect all video generation queues in Redis"""
    print("🔍 Inspecting All Video Generation Queues in Redis")
    print("=" * 60)
    
    load_dotenv()
    
    try:
        # Initialize Redis service
        redis_service = RedisService()
        
        if not redis_service.is_connected():
            print("❌ Redis is not connected")
            return False
        
        client = redis_service.get_client()
        
        # Get all keys that match video queue pattern
        queue_pattern = "video_queue:*"
        queue_keys = client.keys(queue_pattern)
        
        print(f"📊 Found {len(queue_keys)} video generation queues")
        
        if not queue_keys:
            print("📭 No video generation queues found")
            return True
        
        total_items = 0
        
        for queue_key in queue_keys:
            user_id = queue_key.replace("video_queue:", "")
            queue_size = client.zcard(queue_key)
            total_items += queue_size
            
            print(f"\n👤 User: {user_id}")
            print(f"📦 Queue size: {queue_size}")
            
            if queue_size > 0:
                # Get all items in the queue with scores
                queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
                
                print(f"📋 Queue items (showing all {len(queue_items)}):")
                
                existing_videos = 0
                pending_generation = 0
                completed_tasks = 0
                in_progress_tasks = 0
                
                for i, (item_json, score) in enumerate(queue_items):
                    try:
                        item = json.loads(item_json)
                        item_type = item.get("type", "unknown")
                        status = item.get("status", "unknown")
                        
                        # Count by type and status
                        if item_type == "existing_video":
                            existing_videos += 1
                        elif item_type == "generate_video":
                            if status == "pending_generation":
                                pending_generation += 1
                            elif status == "completed":
                                completed_tasks += 1
                            elif status == "in_progress":
                                in_progress_tasks += 1
                        
                        print(f"   {i+1:2d}. [{item_type.upper():15s}] Score: {score:6.2f}")
                        
                        if item_type == "existing_video":
                            video_id = item.get("video_id", "unknown")
                            s3_url = item.get("s3_url", "no url")
                            similarity = item.get("similarity_score", 0)
                            print(f"       Video ID: {video_id}")
                            print(f"       S3 URL: {s3_url[:50]}{'...' if len(s3_url) > 50 else ''}")
                            print(f"       Similarity: {similarity:.3f}")
                            
                        elif item_type == "generate_video":
                            prompt = item.get("prompt", "no prompt")
                            added_at = item.get("added_at", "unknown")
                            print(f"       Status: {status}")
                            print(f"       Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
                            print(f"       Added: {added_at}")
                            
                            if status == "in_progress":
                                started_at = item.get("started_at", "unknown")
                                print(f"       Started: {started_at}")
                            elif status == "completed":
                                video_id = item.get("video_id", "unknown")
                                completed_at = item.get("completed_at", "unknown")
                                print(f"       Video ID: {video_id}")
                                print(f"       Completed: {completed_at}")
                        
                        print()  # Empty line for readability
                        
                    except json.JSONDecodeError:
                        print(f"   {i+1:2d}. [INVALID JSON] Score: {score:6.2f}")
                        print(f"       Raw data: {item_json[:100]}{'...' if len(item_json) > 100 else ''}")
                        print()
                
                # Summary for this queue
                print(f"📈 Queue Summary for {user_id}:")
                print(f"   🎬 Existing videos ready: {existing_videos}")
                print(f"   ⏳ Pending generation: {pending_generation}")
                print(f"   🔄 In progress: {in_progress_tasks}")
                print(f"   ✅ Completed: {completed_tasks}")
        
        print(f"\n" + "=" * 60)
        print(f"🎯 Global Summary:")
        print(f"   📊 Total queues: {len(queue_keys)}")
        print(f"   📦 Total items across all queues: {total_items}")
        
        # Also check if there are any user feed queues
        feed_pattern = "user:feed:*"
        feed_keys = client.keys(feed_pattern)
        print(f"   📺 User feed queues: {len(feed_keys)}")
        
        if feed_keys:
            total_feed_items = 0
            for feed_key in feed_keys:
                feed_size = client.zcard(feed_key)
                total_feed_items += feed_size
            print(f"   📺 Total feed items: {total_feed_items}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting queues: {e}")
        import traceback
        traceback.print_exc()
        return False

def inspect_specific_user_queue(user_id: str):
    """Inspect a specific user's queue"""
    print(f"🔍 Inspecting Video Queue for User: {user_id}")
    print("=" * 60)
    
    load_dotenv()
    
    try:
        redis_service = RedisService()
        
        if not redis_service.is_connected():
            print("❌ Redis is not connected")
            return False
        
        client = redis_service.get_client()
        queue_key = f"video_queue:{user_id}"
        
        queue_size = client.zcard(queue_key)
        print(f"📦 Queue size: {queue_size}")
        
        if queue_size == 0:
            print("📭 Queue is empty")
            return True
        
        # Get all items
        queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
        
        print(f"📋 All items in queue:")
        for i, (item_json, score) in enumerate(queue_items):
            try:
                item = json.loads(item_json)
                print(f"\n{i+1}. Score: {score}")
                print(json.dumps(item, indent=2))
            except json.JSONDecodeError:
                print(f"\n{i+1}. Score: {score} [INVALID JSON]")
                print(f"Raw: {item_json}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting queue: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect Redis video generation queues")
    parser.add_argument("--user", help="Inspect specific user's queue")
    args = parser.parse_args()
    
    if args.user:
        success = inspect_specific_user_queue(args.user)
    else:
        success = inspect_all_video_queues()
    
    if success:
        print("\n✅ Inspection completed!")
    else:
        print("\n❌ Inspection failed!")
        sys.exit(1)
