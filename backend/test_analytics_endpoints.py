#!/usr/bin/env python3
"""
Test analytics endpoints
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_analytics_endpoints():
    """Test all analytics endpoints"""
    
    print("🧪 Testing Analytics Endpoints")
    print("=" * 50)
    
    # Test data
    user_id = "test-user-123"
    video_id = "test-video-456"
    
    # Test 1: Track user interaction (like)
    print("\n1️⃣ Testing User Interaction Tracking...")
    
    interaction_data = {
        "user_id": user_id,
        "video_id": video_id,
        "action": "like",
        "metadata": {
            "source": "mobile_app",
            "session_id": "session-789"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analytics/interaction",
            json=interaction_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Interaction tracked successfully")
            print(f"   Interaction ID: {result['interaction_id']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"   ❌ Failed to track interaction: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Add comment
    print("\n2️⃣ Testing Comment Addition...")
    
    comment_data = {
        "user_id": user_id,
        "video_id": video_id,
        "comment_text": "This is a great video! Love the content."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analytics/comment",
            json=comment_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Comment added successfully")
            print(f"   Comment ID: {result['interaction_id']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"   ❌ Failed to add comment: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Track more interactions
    print("\n3️⃣ Testing Multiple Interactions...")
    
    interactions = [
        {"action": "view", "metadata": {"watch_time": 45}},
        {"action": "share", "metadata": {"platform": "twitter"}},
        {"action": "save", "metadata": {"playlist": "favorites"}}
    ]
    
    for interaction in interactions:
        interaction_data = {
            "user_id": user_id,
            "video_id": video_id,
            **interaction
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/analytics/interaction",
                json=interaction_data
            )
            
            if response.status_code == 200:
                print(f"   ✅ {interaction['action']} tracked successfully")
            else:
                print(f"   ❌ Failed to track {interaction['action']}")
                
        except Exception as e:
            print(f"   ❌ Error tracking {interaction['action']}: {e}")
    
    # Test 4: Get video analytics
    print("\n4️⃣ Testing Video Analytics...")
    
    try:
        response = requests.get(f"{BASE_URL}/analytics/video/{video_id}")
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"   ✅ Video analytics retrieved")
            print(f"   Total views: {analytics['total_views']}")
            print(f"   Total likes: {analytics['total_likes']}")
            print(f"   Total shares: {analytics['total_shares']}")
            print(f"   Total saves: {analytics['total_saves']}")
            print(f"   Total comments: {analytics['total_comments']}")
            print(f"   Engagement rate: {analytics['engagement_rate']}%")
        else:
            print(f"   ❌ Failed to get video analytics: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Get user analytics
    print("\n5️⃣ Testing User Analytics...")
    
    try:
        response = requests.get(f"{BASE_URL}/analytics/user/{user_id}")
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"   ✅ User analytics retrieved")
            print(f"   Total interactions: {analytics['total_interactions']}")
            print(f"   Videos liked: {analytics['videos_liked']}")
            print(f"   Videos commented: {analytics['videos_commented']}")
            print(f"   Videos shared: {analytics['videos_shared']}")
            print(f"   Videos saved: {analytics['videos_saved']}")
        else:
            print(f"   ❌ Failed to get user analytics: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Get video comments
    print("\n6️⃣ Testing Video Comments...")
    
    try:
        response = requests.get(f"{BASE_URL}/analytics/video/{video_id}/comments")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Video comments retrieved")
            print(f"   Total comments: {result['total_comments']}")
            
            for i, comment in enumerate(result['comments'], 1):
                print(f"   Comment {i}: {comment['comment_text'][:50]}...")
        else:
            print(f"   ❌ Failed to get video comments: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Analytics endpoints test completed!")
    print("   Check the results above to verify functionality.")

if __name__ == "__main__":
    test_analytics_endpoints() 