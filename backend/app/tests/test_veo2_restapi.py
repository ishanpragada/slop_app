#!/usr/bin/env python3
"""
Simple Veo 2 Test Script
Uses the google.genai client like your example
"""

import time
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Make sure your API keys are set
# export GEMINI_API_KEY="your-gemini-api-key-here"  # For video generation
# export CLAUDE_API_KEY="your-claude-api-key-here"   # For text generation

load_dotenv()
client = genai.Client()

prompt = """A young boy comes home and asks his parents for a snack, but his parents are busy and tell him to wait."""

print("🎬 Starting Veo 2 video generation...")
print(f"📝 Prompt: {prompt[:50]}...")

operation = client.models.generate_videos(
    model="veo-2.0-generate-001",  # Using Veo 2 instead of Veo 3
    prompt=prompt,
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        aspect_ratio="16:9",
        duration_seconds=8,  # You can choose 5-8 seconds with Veo 2
    )
)

# Poll the operation status until the video is ready
print("⏳ Waiting for video generation to complete...")
while not operation.done:
    print("   Still generating...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Extract video information BEFORE downloading
print("✅ Video generation complete!")
generated_video = operation.response.generated_videos[0]

# 🔗 EXTRACT AND PRINT THE GOOGLE URL
print("\n" + "="*60)
print("📋 VIDEO INFORMATION:")
print("="*60)
print(f"🔗 Google URL (may not work?): {generated_video.video.uri}")
print("="*60)

# Download the generated video
print("\n📥 Downloading video...")
client.files.download(file=generated_video.video)
generated_video.video.save("veo2_dialogue_example_2.mp4")

print("🎉 Generated video saved to veo2_dialogue_example_2.mp4")
print("⚠️  Note: Veo 2 videos are silent (no audio generation)")
print("💡 Tip: For audio, use Veo 3 Fast with 'veo-3.0-fast-generate-preview'")

# Test the URL directly
print(f"\n🧪 Testing direct URL access...")
print(f"   You can access the video directly at:")
print(f"   {generated_video.video.uri}")
print(f"   (This URL will expire after some time!)") 