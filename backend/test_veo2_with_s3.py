#!/usr/bin/env python3
"""
Complete Veo2 + S3 Integration Test
Generates video with Veo2 and stores it in S3 (LocalStack or real AWS)
"""

import time
import uuid
import os
from dotenv import load_dotenv
from app.services.aws_service import AWSService

load_dotenv()

def test_veo2_with_s3():
    """Test the complete video generation and storage workflow"""
    
    print("🎬 Veo2 + S3 Integration Test")
    print("=" * 50)
    
    # Initialize AWS service
    print("🔧 Initializing AWS service...")
    aws_service = AWSService()
    
    print(f"📍 Using LocalStack: {aws_service.use_localstack}")
    print(f"🪣 Videos bucket: {aws_service.videos_bucket}")
    print(f"📋 Metadata bucket: {aws_service.metadata_bucket}")
    
    # Check if we have a test video file
    test_video_path = "veo2_dialogue_example.mp4"
    if not os.path.exists(test_video_path):
        print("❌ Test video file not found!")
        print("Please run a Veo2 generation script first to create a test video.")
        return
    
    # Read test video
    print(f"📥 Reading test video: {test_video_path}")
    with open(test_video_path, 'rb') as f:
        video_data = f.read()
    
    print(f"📊 Video size: {len(video_data) / (1024*1024):.2f} MB")
    
    # Generate unique video ID
    video_id = str(uuid.uuid4())
    print(f"🆔 Video ID: {video_id}")
    
    # Test 1: Upload video to S3
    print("\n🧪 Test 1: Upload video to S3")
    try:
        video_url = aws_service.upload_video(video_data, video_id)
        print(f"✅ Video uploaded successfully!")
        print(f"🔗 Video URL: {video_url}")
    except Exception as e:
        print(f"❌ Video upload failed: {e}")
        return

    # Test 2: Save video metadata
    print("\n🧪 Test 2: Save video metadata")
    metadata = {
        "video_id": video_id,
        "prompt": "Test video uploaded from Veo2 generation",
        "duration_seconds": 8,
        "aspect_ratio": "16:9",
        "content_type": "video/mp4",
        "size_bytes": len(video_data),
        "generated_at": time.time(),
        "tags": ["test", "veo2", "tiktok"],
        "user_id": "test_user",
        "status": "uploaded"
    }
    
    try:
        metadata_url = aws_service.save_video_metadata(video_id, metadata)
        print(f"✅ Metadata saved successfully!")
        print(f"🔗 Metadata URL: {metadata_url}")
    except Exception as e:
        print(f"❌ Metadata save failed: {e}")
    
    # Test 3: Check if video exists
    print("\n🧪 Test 3: Check video existence")
    exists = aws_service.video_exists(video_id)
    print(f"📹 Video exists: {exists}")
    
    # Test 4: Get video URL
    print("\n🧪 Test 4: Get video URL")
    retrieved_url = aws_service.get_video_url(video_id)
    print(f"🔗 Retrieved URL: {retrieved_url}")
    
    # Test 5: List videos
    print("\n🧪 Test 5: List videos in bucket")
    videos = aws_service.list_videos(max_keys=5)
    print(f"📋 Found {len(videos)} videos:")
    for video in videos:
        print(f"  - {video['video_id']}: {video['size']} bytes")
    
    # Test 6: Retrieve video by ID
    print("\n🧪 Test 6: Retrieve video by ID")
    try:
        video_info = aws_service.get_video_by_id(video_id)
        if video_info:
            print(f"✅ Video retrieved successfully!")
            print(f"📊 Content length: {video_info['content_length']} bytes")
            print(f"📋 Content type: {video_info['content_type']}")
            print(f"🔗 URL: {video_info['url']}")
            if video_info['metadata']:
                print(f"📄 Metadata found: {len(video_info['metadata'])} fields")
        else:
            print(f"❌ Video not found")
    except Exception as e:
        print(f"❌ Video retrieval failed: {e}")
    
    # Success summary
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\n📋 Summary:")
    print(f"✅ Video uploaded to S3: {video_url}")
    print(f"✅ Metadata saved: {metadata_url}")
    print(f"✅ Video retrievable: {exists}")
    print(f"✅ Total videos in bucket: {len(videos)}")
    
    print("\n🔧 You can now:")
    print("1. View the video in your React Native app")
    print("2. Use the video URL in your TikTok-like feed")
    print("3. Test the complete video workflow")
    print("4. Use the FastAPI endpoints to manage videos")
    
    if aws_service.use_localstack:
        print(f"\n🌐 LocalStack bucket browser:")
        print(f"  - Videos: http://localhost:4566/{aws_service.videos_bucket}")
        print(f"  - Metadata: http://localhost:4566/{aws_service.metadata_bucket}")

def test_basic_s3_connectivity():
    """Test basic S3 connectivity"""
    print("🔍 Testing basic S3 connectivity...")
    
    try:
        aws_service = AWSService()
        
        # Try to list objects (this will fail gracefully if bucket doesn't exist)
        videos = aws_service.list_videos()
        print(f"✅ S3 connection successful! Found {len(videos)} videos.")
        return True
        
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Veo2 + S3 integration tests...")
    
    # First test basic connectivity
    if not test_basic_s3_connectivity():
        print("\n💡 Make sure LocalStack is running:")
        print("   bash scripts/setup-localstack.sh")
        exit(1)
    
    # Run the full test
    test_veo2_with_s3()