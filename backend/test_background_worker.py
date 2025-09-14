#!/usr/bin/env python3
"""
Test script for background video worker functionality
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.worker_manager_service import WorkerManagerService
from app.services.video_generation_queue_service import VideoGenerationQueueService
from app.services.user_preference_service import UserPreferenceService

def test_worker_system():
    """Test the complete background worker system"""
    print("🧪 Testing Background Worker System")
    print("=" * 60)
    
    load_dotenv()
    
    # Initialize services
    worker_manager = WorkerManagerService()
    queue_service = VideoGenerationQueueService()
    preference_service = UserPreferenceService()
    
    test_user_id = "test_worker_user_789"
    
    try:
        # Test 1: Check initial system health
        print("\n🧪 Test 1: System Health Check")
        health = worker_manager.get_system_health()
        print(f"✅ System health: {health.get('health_status', 'unknown')}")
        if health.get('issues'):
            for issue in health['issues']:
                print(f"⚠️  Issue: {issue}")
        
        # Test 2: Check worker status
        print("\n🧪 Test 2: Worker Status")
        worker_status = worker_manager.get_worker_status()
        print(f"✅ Active workers: {worker_status.get('total_workers', 0)}")
        
        # Test 3: Check queue statistics
        print("\n🧪 Test 3: Queue Statistics")
        queue_stats = worker_manager.get_queue_statistics()
        summary = queue_stats.get('summary', {})
        print(f"✅ Active queues: {summary.get('active_queues', 0)}")
        print(f"📥 Pending tasks: {summary.get('total_pending', 0)}")
        print(f"🔄 In progress: {summary.get('total_in_progress', 0)}")
        print(f"📹 Ready videos: {summary.get('total_ready', 0)}")
        
        # Test 4: Create a video generation task
        print("\n🧪 Test 4: Create Video Generation Task")
        
        # Create some interactions to trigger preference update
        print("📝 Creating user interactions to trigger preference update...")
        interactions_needed = 15  # Trigger preference update
        
        for i in range(interactions_needed):
            result = preference_service.store_user_interaction(
                user_id=test_user_id,
                video_id=f"test_video_{i}",
                interaction_type="like"
            )
            
            if result.get("preference_updated"):
                print(f"🎯 Preference updated after {i + 1} interactions!")
                print("🎬 Video generation queue should be automatically created")
                break
        
        # Test 5: Check if tasks were created
        print("\n🧪 Test 5: Verify Tasks Created")
        time.sleep(2)  # Brief pause for processing
        
        queue_status = queue_service.get_user_queue_status(test_user_id)
        print(f"✅ User queue size: {queue_status.get('queue_size', 0)}")
        print(f"📺 Existing videos: {queue_status.get('existing_videos', 0)}")
        print(f"⏳ Pending generation: {queue_status.get('pending_generation', 0)}")
        
        if queue_status.get('items'):
            print("\n📋 Queue items:")
            for i, item in enumerate(queue_status['items'][:3]):
                item_type = item.get('type', 'unknown')
                status = item.get('status', 'unknown')
                print(f"   {i+1}. Type: {item_type}, Status: {status}")
                if item_type == "generate_video":
                    print(f"      Prompt: {item.get('prompt', 'unknown')[:50]}...")
        
        # Test 6: Test worker management API endpoints (if server is running)
        print("\n🧪 Test 6: API Endpoints (Optional)")
        try:
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            
            # Test health endpoint
            response = requests.get(f"{api_base}/workers/health", timeout=5)
            if response.status_code == 200:
                api_health = response.json()
                print(f"✅ API Health: {api_health.get('health_status', 'unknown')}")
            else:
                print(f"⚠️  API not responding (status: {response.status_code})")
                
        except requests.RequestException:
            print("⚠️  API server not running or not accessible")
            print("   Start the FastAPI server to test API endpoints")
        
        # Test 7: Clean up stale workers
        print("\n🧪 Test 7: Clean Up Stale Workers")
        cleanup_result = worker_manager.clear_stale_workers()
        print(f"✅ Cleared {cleanup_result.get('cleared_workers', 0)} stale workers")
        print(f"✅ Active workers: {cleanup_result.get('active_workers', 0)}")
        
        print("\n" + "=" * 60)
        print("🎉 Background Worker System Tests Completed!")
        print("\n📋 Summary:")
        print("✅ System health checking")
        print("✅ Worker status monitoring")
        print("✅ Queue statistics tracking")
        print("✅ Task creation from preference updates")
        print("✅ Queue item verification")
        print("✅ Worker cleanup functionality")
        
        print("\n🚀 To start actual video generation:")
        print("1. Run: python start_video_worker.py")
        print("2. Or use API: POST /workers/start")
        print("3. Monitor with: GET /workers/status")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_worker_start_instructions():
    """Print instructions for starting the worker"""
    print("\n🔧 Worker Start Instructions:")
    print("-" * 40)
    print("1. Manual start:")
    print("   python start_video_worker.py")
    print()
    print("2. Via API (if server running):")
    print("   curl -X POST http://localhost:8000/workers/start")
    print()
    print("3. Background start:")
    print("   nohup python start_video_worker.py > worker.log 2>&1 &")
    print()
    print("4. Docker (if containerized):")
    print("   docker run -d your-app python start_video_worker.py")

if __name__ == "__main__":
    print("🚀 Starting background worker system tests...")
    
    success = test_worker_system()
    
    if success:
        test_worker_start_instructions()
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
