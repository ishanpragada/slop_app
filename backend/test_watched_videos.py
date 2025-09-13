#!/usr/bin/env python3
"""
Test script for watched videos functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.user_preference_service import UserPreferenceService

def test_watched_videos():
    """Test the watched videos functionality"""
    print("🧪 Testing Watched Videos Functionality")
    print("=" * 50)
    
    load_dotenv()
    
    # Initialize service
    user_preference_service = UserPreferenceService()
    
    # Test user ID
    test_user_id = "test_user_123"
    test_video_id_1 = "video_001"
    test_video_id_2 = "video_002"
    test_video_id_3 = "video_003"
    
    print(f"🔧 Testing with user: {test_user_id}")
    
    try:
        # Test 1: Get watched videos for new user (should be empty)
        print("\n🧪 Test 1: Get watched videos for new user")
        watched_videos = user_preference_service.get_watched_videos(test_user_id)
        print(f"✅ Initial watched videos: {watched_videos}")
        assert watched_videos == [], f"Expected empty list, got {watched_videos}"
        
        # Test 2: Add a video to watched list
        print("\n🧪 Test 2: Add video to watched list")
        success = user_preference_service.add_watched_video(test_user_id, test_video_id_1)
        print(f"✅ Add video result: {success}")
        assert success, "Failed to add video to watched list"
        
        # Test 3: Check if video is in watched list
        print("\n🧪 Test 3: Check if video is watched")
        has_watched = user_preference_service.has_watched_video(test_user_id, test_video_id_1)
        print(f"✅ Has watched video: {has_watched}")
        assert has_watched, "Video should be marked as watched"
        
        # Test 4: Get updated watched videos list
        print("\n🧪 Test 4: Get updated watched videos list")
        watched_videos = user_preference_service.get_watched_videos(test_user_id)
        print(f"✅ Updated watched videos: {watched_videos}")
        assert test_video_id_1 in watched_videos, f"Video {test_video_id_1} should be in watched list"
        
        # Test 5: Add multiple videos
        print("\n🧪 Test 5: Add multiple videos")
        user_preference_service.add_watched_video(test_user_id, test_video_id_2)
        user_preference_service.add_watched_video(test_user_id, test_video_id_3)
        
        watched_videos = user_preference_service.get_watched_videos(test_user_id)
        print(f"✅ Multiple watched videos: {watched_videos}")
        assert len(watched_videos) == 3, f"Expected 3 videos, got {len(watched_videos)}"
        
        # Test 6: Try to add duplicate video (should not duplicate)
        print("\n🧪 Test 6: Add duplicate video")
        user_preference_service.add_watched_video(test_user_id, test_video_id_1)
        watched_videos = user_preference_service.get_watched_videos(test_user_id)
        print(f"✅ After duplicate add: {watched_videos}")
        assert len(watched_videos) == 3, f"Expected 3 videos (no duplicates), got {len(watched_videos)}"
        
        # Test 7: Filter unwatched videos from list
        print("\n🧪 Test 7: Filter unwatched videos")
        all_videos = [test_video_id_1, test_video_id_2, test_video_id_3, "video_004", "video_005"]
        unwatched = user_preference_service.get_unwatched_videos_from_list(test_user_id, all_videos)
        print(f"✅ Unwatched videos: {unwatched}")
        expected_unwatched = ["video_004", "video_005"]
        assert unwatched == expected_unwatched, f"Expected {expected_unwatched}, got {unwatched}"
        
        # Test 8: Remove a video from watched list
        print("\n🧪 Test 8: Remove video from watched list")
        success = user_preference_service.remove_watched_video(test_user_id, test_video_id_2)
        print(f"✅ Remove video result: {success}")
        assert success, "Failed to remove video from watched list"
        
        watched_videos = user_preference_service.get_watched_videos(test_user_id)
        print(f"✅ After removal: {watched_videos}")
        assert test_video_id_2 not in watched_videos, f"Video {test_video_id_2} should be removed"
        assert len(watched_videos) == 2, f"Expected 2 videos after removal, got {len(watched_videos)}"
        
        # Test 9: Get user preference with watched videos
        print("\n🧪 Test 9: Get user preference with watched videos")
        preference = user_preference_service.get_user_preference(test_user_id)
        if preference:
            print(f"✅ User preference watched videos: {preference.watched_videos}")
            assert len(preference.watched_videos) == 2, f"Expected 2 watched videos in preference, got {len(preference.watched_videos)}"
        else:
            print("⚠️  User preference not found (this is ok for new users)")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("\n📋 Test Summary:")
        print("✅ Added videos to watched list")
        print("✅ Checked video watch status")
        print("✅ Prevented duplicate entries")
        print("✅ Filtered unwatched videos")
        print("✅ Removed videos from watched list")
        print("✅ Retrieved user preferences with watched videos")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting watched videos tests...")
    success = test_watched_videos()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
