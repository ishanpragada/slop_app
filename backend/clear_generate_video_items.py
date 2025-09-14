#!/usr/bin/env python3
"""
Script to remove all GENERATE_VIDEO items from Redis video generation queues
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.redis_service import RedisService

def remove_generate_video_items():
    """Remove all GENERATE_VIDEO items from all video generation queues"""
    print("🧹 Removing All GENERATE_VIDEO Items from Redis Queues")
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
        total_remaining = 0
        
        for queue_key in queue_keys:
            user_id = queue_key.replace("video_queue:", "")
            queue_size = client.zcard(queue_key)
            
            print(f"\n👤 Processing User: {user_id}")
            print(f"📦 Initial queue size: {queue_size}")
            
            if queue_size == 0:
                print("📭 Queue is empty, skipping")
                continue
            
            # Get all items in the queue
            queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            items_to_remove = []
            items_to_keep = []
            generate_video_count = 0
            existing_video_count = 0
            
            # Separate GENERATE_VIDEO items from others
            for item_json, score in queue_items:
                try:
                    item = json.loads(item_json)
                    item_type = item.get("type", "unknown")
                    
                    if item_type == "generate_video":
                        items_to_remove.append((item_json, score))
                        generate_video_count += 1
                        
                        # Show which item we're removing
                        status = item.get("status", "unknown")
                        prompt = item.get("prompt", "no prompt")
                        print(f"   🗑️  Removing: [{status.upper()}] {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
                        
                    else:
                        items_to_keep.append((item_json, score))
                        if item_type == "existing_video":
                            existing_video_count += 1
                        
                except json.JSONDecodeError:
                    # Keep invalid JSON items as-is (shouldn't happen but be safe)
                    items_to_keep.append((item_json, score))
                    print(f"   ⚠️  Keeping invalid JSON item")
            
            # Remove GENERATE_VIDEO items from Redis
            if items_to_remove:
                for item_json, _ in items_to_remove:
                    result = client.zrem(queue_key, item_json)
                    if result:
                        total_removed += 1
                
                print(f"   ✅ Removed {generate_video_count} GENERATE_VIDEO items")
            else:
                print(f"   ℹ️  No GENERATE_VIDEO items found")
            
            # Show final state
            final_queue_size = client.zcard(queue_key)
            total_remaining += final_queue_size
            print(f"   📊 Final queue size: {final_queue_size} (kept {existing_video_count} existing videos)")
        
        print(f"\n" + "=" * 60)
        print(f"🎯 Operation Summary:")
        print(f"   📊 Queues processed: {len(queue_keys)}")
        print(f"   🗑️  Total GENERATE_VIDEO items removed: {total_removed}")
        print(f"   📦 Total items remaining: {total_remaining}")
        
        # Verify by checking final state
        print(f"\n🔍 Verification - checking for remaining GENERATE_VIDEO items:")
        remaining_generate_videos = 0
        
        for queue_key in queue_keys:
            queue_items = client.zrevrange(queue_key, 0, -1)
            
            for item_json in queue_items:
                try:
                    item = json.loads(item_json)
                    if item.get("type") == "generate_video":
                        remaining_generate_videos += 1
                        print(f"   ⚠️  Found remaining GENERATE_VIDEO in {queue_key}")
                except json.JSONDecodeError:
                    continue
        
        if remaining_generate_videos == 0:
            print(f"   ✅ Verification passed: No GENERATE_VIDEO items remain")
        else:
            print(f"   ❌ Verification failed: {remaining_generate_videos} GENERATE_VIDEO items still found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing GENERATE_VIDEO items: {e}")
        import traceback
        traceback.print_exc()
        return False

def remove_generate_video_items_for_user(user_id: str):
    """Remove GENERATE_VIDEO items from a specific user's queue"""
    print(f"🧹 Removing GENERATE_VIDEO Items for User: {user_id}")
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
        
        # Get all items
        queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
        
        items_removed = 0
        
        for item_json, score in queue_items:
            try:
                item = json.loads(item_json)
                if item.get("type") == "generate_video":
                    result = client.zrem(queue_key, item_json)
                    if result:
                        items_removed += 1
                        status = item.get("status", "unknown")
                        prompt = item.get("prompt", "no prompt")
                        print(f"   🗑️  Removed: [{status.upper()}] {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            except json.JSONDecodeError:
                continue
        
        final_size = client.zcard(queue_key)
        print(f"✅ Removed {items_removed} GENERATE_VIDEO items")
        print(f"📊 Final queue size: {final_size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing GENERATE_VIDEO items: {e}")
        import traceback
        traceback.print_exc()
        return False

def confirm_operation():
    """Ask user to confirm the destructive operation"""
    print("⚠️  WARNING: This operation will permanently remove all GENERATE_VIDEO items!")
    print("   This includes:")
    print("   - Items with status: pending_generation")
    print("   - Items with status: in_progress") 
    print("   - Items with status: completed")
    print("   - Any other GENERATE_VIDEO items")
    print()
    print("   EXISTING_VIDEO items will be preserved.")
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
    
    parser = argparse.ArgumentParser(description="Remove GENERATE_VIDEO items from Redis queues")
    parser.add_argument("--user", help="Remove items from specific user's queue only")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    if not args.force:
        if not confirm_operation():
            print("❌ Operation cancelled by user")
            sys.exit(0)
    
    print("🚀 Starting removal operation...")
    
    if args.user:
        success = remove_generate_video_items_for_user(args.user)
    else:
        success = remove_generate_video_items()
    
    if success:
        print("\n✅ Removal operation completed successfully!")
    else:
        print("\n❌ Removal operation failed!")
        sys.exit(1)
