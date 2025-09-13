#!/usr/bin/env python3
"""
Test script for the new get_video_by_id functionality
"""

import os
import uuid
from dotenv import load_dotenv
from app.services.aws_service import AWSService

load_dotenv()

def test_video_retrieval():
    """Test the get_video_by_id function"""
    
    print("🎬 Testing Video Retrieval Functionality")
    print("=" * 50)
    
    # Initialize AWS service
    aws_service = AWSService()
    
    # Generate a test video ID (UUID format)
    test_video_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    print(f"🆔 Test video ID: {test_video_id}")
    
    # Test 1: Try to retrieve a non-existent video
    print("\n🧪 Test 1: Retrieve non-existent video")
    try:
        video_info = aws_service.get_video_by_id(test_video_id)
        if video_info is None:
            print("✅ Correctly returned None for non-existent video")
        else:
            print("❌ Should have returned None for non-existent video")
    except Exception as e:
        print(f"❌ Error retrieving non-existent video: {e}")
    
    # Test 2: Try with video_id without .mp4 extension
    print("\n🧪 Test 2: Retrieve with ID without .mp4 extension")
    try:
        video_info = aws_service.get_video_by_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        if video_info is None:
            print("✅ Correctly returned None for non-existent video (without .mp4)")
        else:
            print("❌ Should have returned None for non-existent video (without .mp4)")
    except Exception as e:
        print(f"❌ Error retrieving video without .mp4: {e}")
    
    # Test 3: Check if any videos exist in the bucket
    print("\n🧪 Test 3: Check existing videos in bucket")
    try:
        videos = aws_service.list_videos(max_keys=5)
        print(f"📋 Found {len(videos)} videos in bucket")
        
        if videos:
            # Test 4: Try to retrieve the first existing video
            first_video_id = videos[0]['video_id']
            print(f"\n🧪 Test 4: Retrieve existing video: {first_video_id}")
            
            try:
                video_info = aws_service.get_video_by_id(first_video_id)
                if video_info:
                    print("✅ Successfully retrieved existing video!")
                    print(f"📊 Content length: {video_info['content_length']} bytes")
                    print(f"📋 Content type: {video_info['content_type']}")
                    print(f"🔗 URL: {video_info['url']}")
                    print(f"📄 Metadata: {video_info['metadata'] is not None}")
                else:
                    print("❌ Failed to retrieve existing video")
            except Exception as e:
                print(f"❌ Error retrieving existing video: {e}")
        else:
            print("ℹ️  No videos found in bucket to test retrieval")
            
    except Exception as e:
        print(f"❌ Error listing videos: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Video retrieval tests completed!")

if __name__ == "__main__":
    test_video_retrieval() 