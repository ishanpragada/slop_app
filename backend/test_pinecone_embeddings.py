#!/usr/bin/env python3
"""
Test script for Pinecone embeddings functionality
"""

import os
import uuid
from dotenv import load_dotenv
from app.services.pinecone_service import PineconeService

def test_pinecone_embeddings():
    """Test the Pinecone embeddings service"""
    
    print("🎬 Testing Pinecone Embeddings Service")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please add them to your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return
    
    try:
        # Initialize Pinecone service
        print("\n1️⃣ Initializing Pinecone Service...")
        pinecone_service = PineconeService()
        print("✅ Pinecone service initialized successfully")
        
        # Test 1: Add sample embeddings
        print("\n2️⃣ Testing Embedding Addition...")
        print("-" * 30)
        
        test_prompts = [
            "A cinematic shot of a cat playing with yarn in golden hour lighting",
            "A dramatic close-up of someone cooking and accidentally adding salt instead of sugar",
            "A tracking shot of a person trying to parallel park and failing spectacularly",
            "A warm, intimate scene of someone discovering their phone in their pocket after searching everywhere",
            "A dynamic shot of someone trying to take a selfie with a group but everyone keeps moving"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            video_id = str(uuid.uuid4())
            s3_url = f"https://slop-videos.s3.amazonaws.com/videos/{video_id}.mp4"
            
            print(f"\n   Adding embedding {i}/{len(test_prompts)}...")
            result = pinecone_service.add_prompt_embedding(
                prompt=prompt,
                video_id=video_id,
                s3_url=s3_url,
                metadata={
                    "style": "cinematic",
                    "category": "slice_of_life",
                    "duration_seconds": 8
                }
            )
            
            if result["success"]:
                print(f"   ✅ Added embedding for video {video_id[:8]}...")
            else:
                print(f"   ❌ Failed to add embedding: {result.get('error', 'Unknown error')}")
        
        # Test 2: Get index statistics
        print("\n3️⃣ Testing Index Statistics...")
        print("-" * 30)
        stats = pinecone_service.get_index_stats()
        print(f"✅ Index stats: {stats}")
        
        # Test 3: Find similar prompts
        print("\n4️⃣ Testing Similarity Search...")
        print("-" * 30)
        
        query_prompt = "A cat playing with yarn in warm lighting"
        print(f"   Searching for prompts similar to: '{query_prompt}'")
        
        similar_prompts = pinecone_service.find_similar_prompts(
            query_prompt=query_prompt,
            k=3
        )
        
        print(f"   ✅ Found {len(similar_prompts)} similar prompts:")
        for i, result in enumerate(similar_prompts, 1):
            print(f"   {i}. Score: {result['similarity_score']:.3f}")
            print(f"      Prompt: {result['prompt'][:80]}...")
            print(f"      Video ID: {result['metadata']['video_id'][:8]}...")
            print()
        
        # Test 4: Test with different query
        print("\n5️⃣ Testing Another Similarity Search...")
        print("-" * 30)
        
        query_prompt2 = "Someone cooking and making a mistake in the kitchen"
        print(f"   Searching for prompts similar to: '{query_prompt2}'")
        
        similar_prompts2 = pinecone_service.find_similar_prompts(
            query_prompt=query_prompt2,
            k=3
        )
        
        print(f"   ✅ Found {len(similar_prompts2)} similar prompts:")
        for i, result in enumerate(similar_prompts2, 1):
            print(f"   {i}. Score: {result['similarity_score']:.3f}")
            print(f"      Prompt: {result['prompt'][:80]}...")
            print(f"      Video ID: {result['metadata']['video_id'][:8]}...")
            print()
        
        print("\n🎉 Pinecone embeddings testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pinecone_embeddings()
