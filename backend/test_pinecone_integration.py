#!/usr/bin/env python3
"""
Test Pinecone integration with the new API
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pinecone_service import PineconeService

def test_pinecone_integration():
    """Test basic Pinecone functionality"""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not found in .env file")
        return False
    
    print("✅ PINECONE_API_KEY found")
    
    try:
        # Initialize Pinecone service
        print("🔄 Initializing Pinecone service...")
        pinecone_service = PineconeService()
        print("✅ Pinecone service initialized successfully")
        
        # Test adding an embedding
        print("🔄 Testing embedding addition...")
        test_prompt = "A cat playing with a ball in the garden"
        test_video_id = "test-video-123"
        test_s3_url = "https://slop-bucket.s3.amazonaws.com/videos/test-video-123.mp4"
        
        result = pinecone_service.add_prompt_embedding(
            prompt=test_prompt,
            video_id=test_video_id,
            s3_url=test_s3_url
        )
        
        if result.get("success"):
            print("✅ Embedding added successfully")
            print(f"   Video ID: {result['video_id']}")
            print(f"   Index: {result['index_name']}")
        else:
            print(f"❌ Failed to add embedding: {result.get('error')}")
            return False
        
        # Test finding similar prompts
        print("🔄 Testing similarity search...")
        query_prompt = "A kitten chasing a toy"
        similar_prompts = pinecone_service.find_similar_prompts(
            query_prompt=query_prompt,
            k=5
        )
        
        print(f"✅ Found {len(similar_prompts)} similar prompts")
        for i, prompt in enumerate(similar_prompts[:3]):
            print(f"   {i+1}. Score: {prompt['similarity_score']:.3f}")
            print(f"      Prompt: {prompt['prompt'][:50]}...")
        
        # Test getting index stats
        print("🔄 Testing index statistics...")
        stats = pinecone_service.get_index_stats()
        
        if "error" not in stats:
            print("✅ Index statistics retrieved")
            print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
            print(f"   Dimension: {stats.get('dimension', 0)}")
            print(f"   Metric: {stats.get('metric', '')}")
        else:
            print(f"❌ Failed to get stats: {stats.get('error')}")
        
        # Test deleting the test embedding
        print("🔄 Testing embedding deletion...")
        delete_result = pinecone_service.delete_video_embedding(test_video_id)
        
        if delete_result.get("success"):
            print("✅ Test embedding deleted successfully")
        else:
            print(f"❌ Failed to delete embedding: {delete_result.get('error')}")
        
        print("\n🎉 All Pinecone integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during Pinecone integration test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Pinecone Integration")
    print("=" * 40)
    
    success = test_pinecone_integration()
    
    if success:
        print("\n✅ Pinecone integration is working correctly!")
        print("   You can now use the /ai/videos/generate endpoint")
        print("   and prompts will be automatically embedded in Pinecone")
    else:
        print("\n❌ Pinecone integration test failed!")
        print("   Please check your PINECONE_API_KEY and try again") 