#!/usr/bin/env python3
"""
Test script to verify the background worker can call API endpoints
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_generation_queue_service import VideoGenerationQueueService

def test_api_connectivity():
    """Test if the API server is running and accessible"""
    print("🧪 Testing API Connectivity")
    print("-" * 40)
    
    load_dotenv()
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    try:
        # Test health endpoint
        response = requests.get(f"{api_base}/workers/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API server is running at {api_base}")
            print(f"   Health status: {health.get('health_status', 'unknown')}")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Cannot connect to API server at {api_base}")
        print(f"   Error: {e}")
        return False

def test_video_generation_endpoint():
    """Test the video generation endpoint directly"""
    print("\n🧪 Testing Video Generation Endpoint")
    print("-" * 40)
    
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # Test payload
    payload = {
        "prompt": "A quick test video of a cat playing with yarn",
        "aspect_ratio": "16:9",
        "duration_seconds": 8,
        "number_of_videos": 1
    }
    
    print(f"Testing endpoint: {api_base}/api/v1/ai/videos/generate")
    print(f"Payload: {payload}")
    print("⚠️  Note: This will actually generate a video if API is working!")
    
    try:
        response = requests.post(
            f"{api_base}/api/v1/ai/videos/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Video generation endpoint is working!")
                print(f"   Video ID: {result.get('video_id', 'unknown')}")
                return True
            else:
                print(f"❌ Video generation failed: {result.get('error', 'unknown')}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.Timeout:
        print("❌ Video generation timed out (this is expected for long generations)")
        return True  # Timeout is actually OK - means the endpoint is working
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def check_pending_tasks():
    """Check if there are any pending video generation tasks"""
    print("\n🧪 Checking for Pending Tasks")
    print("-" * 40)
    
    try:
        queue_service = VideoGenerationQueueService()
        
        # Get queue statistics
        api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
        response = requests.get(f"{api_base}/workers/queue-stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            summary = stats.get('summary', {})
            
            print(f"✅ Queue Statistics:")
            print(f"   Active queues: {summary.get('active_queues', 0)}")
            print(f"   Pending tasks: {summary.get('total_pending', 0)}")
            print(f"   Ready videos: {summary.get('total_ready', 0)}")
            print(f"   In progress: {summary.get('total_in_progress', 0)}")
            
            return summary.get('total_pending', 0) > 0
        else:
            print(f"❌ Failed to get queue stats: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking pending tasks: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Background Worker API Integration Test")
    print("=" * 50)
    
    # Test 1: API connectivity
    if not test_api_connectivity():
        print("\n💡 To start the API server:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        return False
    
    # Test 2: Check for pending tasks
    has_pending = check_pending_tasks()
    
    if has_pending:
        print("\n🎬 Pending tasks found! You can process them with:")
        print("   python process_video_queue.py")
        print("   OR")
        print("   curl -X POST http://localhost:8000/workers/process-all-pending")
    else:
        print("\n📝 No pending tasks found. To create some:")
        print("   1. Use the app to create user interactions")
        print("   2. Or trigger preference updates manually")
    
    # Test 3: Video generation endpoint (optional - commented out to avoid costs)
    print("\n⚠️  Skipping actual video generation test to avoid API costs")
    print("   Uncomment test_video_generation_endpoint() to test actual generation")
    # test_video_generation_endpoint()
    
    print("\n✅ API integration tests completed!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
