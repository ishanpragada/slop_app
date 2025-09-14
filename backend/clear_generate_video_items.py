#!/usr/bin/env python3
"""
Script to remove all items from Redis video generation queues
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.redis_service import RedisService

def remove_all_queue_items():
    """Remove all items from all video generation queues"""
    print("🧹 Removing All Items from Redis Queues")
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
        
        total_removed = 0
        
        for queue_key in queue_keys:
            user_id = queue_key.replace("video_queue:", "")
            queue_size = client.zcard(queue_key)
            
            print(f"\n👤 Processing User: {user_id}")
            print(f"📦 Initial queue size: {queue_size}")
            
            if queue_size == 0:
                print("📭 Queue is empty, skipping")
                continue
            
            # Get all items in the queue for display purposes
            queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            # Show which items we're removing
            for item_json, score in queue_items:
                try:
                    item = json.loads(item_json)
                    item_type = item.get("type", "unknown")
                    
                    if item_type == "generate_video":
                        status = item.get("status", "unknown")
                        prompt = item.get("prompt", "no prompt")
                        print(f"   🗑️  Removing: [{item_type.upper()}] [{status.upper()}] {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
                    elif item_type == "existing_video":
                        video_id = item.get("video_id", "unknown")
                        print(f"   🗑️  Removing: [{item_type.upper()}] Video ID: {video_id}")
                    else:
                        print(f"   🗑️  Removing: [{item_type.upper()}] Item")
                        
                except json.JSONDecodeError:
                    print(f"   🗑️  Removing: [INVALID JSON] Item")
            
            # Remove ALL items from the queue
            removed_count = client.delete(queue_key)
            if removed_count:
                total_removed += queue_size
                print(f"   ✅ Removed all {queue_size} items from queue")
            else:
                print(f"   ⚠️  Failed to remove items from queue")
        
        print(f"\n" + "=" * 60)
        print(f"🎯 Operation Summary:")
        print(f"   📊 Queues processed: {len(queue_keys)}")
        print(f"   🗑️  Total items removed: {total_removed}")
        
        # Verify by checking final state
        print(f"\n🔍 Verification - checking for remaining items:")
        remaining_queues = 0
        
        # Re-check queue keys to see if any still exist
        remaining_queue_keys = client.keys(queue_pattern)
        
        for queue_key in remaining_queue_keys:
            queue_size = client.zcard(queue_key)
            if queue_size > 0:
                remaining_queues += 1
                print(f"   ⚠️  Queue {queue_key} still has {queue_size} items")
        
        if remaining_queues == 0:
            print(f"   ✅ Verification passed: All queues cleared")
        else:
            print(f"   ❌ Verification failed: {remaining_queues} queues still have items")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing queue items: {e}")
        import traceback
        traceback.print_exc()
        return False

def remove_all_queue_items_for_user(user_id: str):
    """Remove all items from a specific user's queue"""
    print(f"🧹 Removing All Items for User: {user_id}")
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
        print(f"📦 Initial queue size: {queue_size}")
        
        if queue_size == 0:
            print("📭 Queue is empty")
            return True
        
        # Get all items for display purposes
        queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
        
        # Show which items we're removing
        for item_json, score in queue_items:
            try:
                item = json.loads(item_json)
                item_type = item.get("type", "unknown")
                
                if item_type == "generate_video":
                    status = item.get("status", "unknown")
                    prompt = item.get("prompt", "no prompt")
                    print(f"   🗑️  Removing: [{item_type.upper()}] [{status.upper()}] {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
                elif item_type == "existing_video":
                    video_id = item.get("video_id", "unknown")
                    print(f"   🗑️  Removing: [{item_type.upper()}] Video ID: {video_id}")
                else:
                    print(f"   🗑️  Removing: [{item_type.upper()}] Item")
            except json.JSONDecodeError:
                print(f"   🗑️  Removing: [INVALID JSON] Item")
        
        # Remove ALL items from the queue
        removed_count = client.delete(queue_key)
        if removed_count:
            print(f"✅ Removed all {queue_size} items from queue")
        else:
            print(f"⚠️  Failed to remove items from queue")
        
        final_size = client.zcard(queue_key)
        print(f"📊 Final queue size: {final_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing queue items: {e}")
        import traceback
        traceback.print_exc()
        return False

def confirm_operation():
    """Ask user to confirm the destructive operation"""
    print("⚠️  WARNING: This operation will permanently remove ALL items from Redis queues!")
    print("   This includes:")
    print("   - All GENERATE_VIDEO items (pending, in_progress, completed)")
    print("   - All EXISTING_VIDEO items") 
    print("   - Any other queue items")
    print()
    print("   This will COMPLETELY CLEAR all video generation queues!")
    print()
    
    while True:
        response = input("Do you want to continue? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove all items from Redis queues")
    parser.add_argument("--user", help="Remove items from specific user's queue only")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    if not args.force:
        if not confirm_operation():
            print("❌ Operation cancelled by user")
            sys.exit(0)
    
    print("🚀 Starting removal operation...")
    
    if args.user:
        success = remove_all_queue_items_for_user(args.user)
    else:
        success = remove_all_queue_items()
    
    if success:
        print("\n✅ Removal operation completed successfully!")
    else:
        print("\n❌ Removal operation failed!")
        sys.exit(1)
