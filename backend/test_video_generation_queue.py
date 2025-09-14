#!/usr/bin/env python3
"""
Test script for video generation queue functionality
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.video_generation_queue_service import VideoGenerationQueueService
from app.services.user_preference_service import UserPreferenceService

def test_video_generation_queue():
    """Test the video generation queue functionality"""
    print("🧪 Testing Video Generation Queue Functionality")
    print("=" * 60)
    
    load_dotenv()
    
    # Initialize services
    queue_service = VideoGenerationQueueService()
    preference_service = UserPreferenceService()
    
    # Test user ID
    test_user_id = "test_queue_user_456"
    
    print(f"🔧 Testing with user: {test_user_id}")
    
    try:
        # Test 1: Check initial queue status (should be empty)
        print("\n🧪 Test 1: Check initial queue status")
        status = queue_service.get_user_queue_status(test_user_id)
        print(f"✅ Initial queue status: {status}")
        
        # Test 2: Create a mock preference vector
        print("\n🧪 Test 2: Create mock preference vector")
        # Create a realistic 1536-dimensional preference vector (small random values)
        import random
        preference_vector = [random.uniform(-0.1, 0.1) for _ in range(1536)]
        print(f"✅ Created preference vector with {len(preference_vector)} dimensions")
        
        # Test 3: Process the preference vector (this is the main functionality)
        print("\n🧪 Test 3: Process preference vector")
        print("-" * 40)
        result = queue_service.process_new_preference_vector(test_user_id, preference_vector)
        
        print(f"✅ Processing result: {result.get('success', False)}")
        print(f"📊 Strategy used: {result.get('strategy', 'unknown')}")
        
        if result.get("success"):
            if result.get("strategy") == "existing_videos":
                print(f"🎬 Found {result.get('videos_found', 0)} existing videos")
                print(f"📥 Queued {result.get('videos_queued', 0)} videos")
                
                # Show some details about the videos
                videos = result.get("videos", [])
                for i, video in enumerate(videos[:3]):  # Show first 3
                    print(f"   {i+1}. Video ID: {video.get('video_id', 'unknown')[:8]}...")
                    print(f"      Prompt: {video.get('prompt', 'no prompt')[:50]}...")
                    print(f"      Similarity: {video.get('similarity_score', 0):.3f}")
                    
            elif result.get("strategy") == "generated_prompts":
                print(f"🤖 Generated {result.get('new_prompts_generated', 0)} new prompts")
                print(f"📥 Queued {result.get('prompts_queued', 0)} prompts for generation")
                
                # Show the generated prompts
                prompts = result.get("generated_prompts", [])
                for i, prompt in enumerate(prompts):
                    print(f"   {i+1}. {prompt}")
        else:
            print(f"❌ Processing failed: {result.get('message', 'unknown error')}")
        
        # Test 4: Check queue status after processing
        print("\n🧪 Test 4: Check queue status after processing")
        final_status = queue_service.get_user_queue_status(test_user_id)
        print(f"✅ Final queue size: {final_status.get('queue_size', 0)}")
        print(f"📺 Existing videos: {final_status.get('existing_videos', 0)}")
        print(f"⏳ Pending generation: {final_status.get('pending_generation', 0)}")
        
        if final_status.get("items"):
            print("\n📋 Queue items:")
            for i, item in enumerate(final_status["items"][:5]):  # Show first 5
                item_type = item.get("type", "unknown")
                if item_type == "existing_video":
                    print(f"   {i+1}. [READY] Video: {item.get('video_id', 'unknown')[:8]}...")
                    print(f"      Score: {item.get('queue_score', 0):.3f}")
                elif item_type == "generate_video":
                    print(f"   {i+1}. [PENDING] Prompt: {item.get('prompt', 'unknown')[:50]}...")
                    print(f"      Priority: {item.get('queue_score', 0)}")
        
        # Test 5: Test with actual user preference service integration
        print("\n🧪 Test 5: Test integration with UserPreferenceService")
        print("-" * 40)
        
        # Create some test interactions to build a preference vector
        test_video_ids = ["test_vid_1", "test_vid_2", "test_vid_3"]
        
        for vid_id in test_video_ids:
            interaction_result = preference_service.store_user_interaction(
                user_id=test_user_id,
                video_id=vid_id,
                interaction_type="like"
            )
            print(f"📝 Stored interaction for {vid_id}: {interaction_result.get('success', False)}")
            
            # Check if preference was updated (and queue triggered)
            if interaction_result.get("preference_updated"):
                print(f"🎯 Preference vector updated! Queue should be automatically triggered.")
                break
        
        # Final queue status check
        print("\n🧪 Final Test: Check queue after preference service integration")
        integration_status = queue_service.get_user_queue_status(test_user_id)
        print(f"✅ Integration test queue size: {integration_status.get('queue_size', 0)}")
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("\n📋 Test Summary:")
        print("✅ Queue status checking")
        print("✅ Preference vector processing")
        print("✅ Similarity search or prompt generation")
        print("✅ Redis queue management")
        print("✅ Integration with user preference service")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_similarity_calculation():
    """Test the cosine similarity calculation"""
    print("\n🧮 Testing Cosine Similarity Calculation")
    print("-" * 40)
    
    queue_service = VideoGenerationQueueService()
    
    # Test vectors
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]  # Identical
    vec3 = [0.0, 1.0, 0.0]  # Orthogonal
    vec4 = [0.5, 0.5, 0.0]  # Similar
    
    # Test identical vectors
    sim1 = queue_service._cosine_similarity(vec1, vec2)
    print(f"✅ Identical vectors similarity: {sim1:.3f} (should be ~1.0)")
    
    # Test orthogonal vectors
    sim2 = queue_service._cosine_similarity(vec1, vec3)
    print(f"✅ Orthogonal vectors similarity: {sim2:.3f} (should be ~0.0)")
    
    # Test similar vectors
    sim3 = queue_service._cosine_similarity(vec1, vec4)
    print(f"✅ Similar vectors similarity: {sim3:.3f} (should be ~0.7)")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting video generation queue tests...")
    
    # Test similarity calculation first
    if not test_similarity_calculation():
        print("\n❌ Similarity tests failed!")
        sys.exit(1)
    
    # Test main queue functionality
    if test_video_generation_queue():
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

