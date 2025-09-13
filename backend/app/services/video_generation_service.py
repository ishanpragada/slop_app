import os
import time
import uuid
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.models.video_generation_models import VideoGenerationResult
from app.services.pinecone_service import PineconeService

class VideoGenerationService:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()
        # Create downloads directory if it doesn't exist
        self.downloads_dir = "downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def generate_video_complete(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        number_of_videos: int = 1,
        upload_to_s3: bool = False,
        aws_service = None,
        pinecone_service: PineconeService = None
    ) -> VideoGenerationResult:
        """
        Complete video generation workflow - generates video, waits for completion, and optionally uploads to S3
        
        Args:
            prompt: Text description for video generation
            aspect_ratio: Video aspect ratio (default: "16:9")
            duration_seconds: Video duration in seconds (fixed at 8 seconds for Veo 3 Fast)
            number_of_videos: Number of videos to generate
            upload_to_s3: Whether to upload video to S3 (default: False)
            aws_service: AWS service instance for S3 upload (required if upload_to_s3=True)
            
        Returns:
            VideoGenerationResult containing complete generation results and video data
        """
        try:
            # Generate unique operation ID for tracking
            operation_id = str(uuid.uuid4())
            
            # Step 1: Start video generation
            print(f"🚀 Starting video generation for prompt: '{prompt}'")
            
            # Veo 3 Fast has a fixed duration and doesn't support duration_seconds parameter
            model_name = "veo-3.0-fast-generate-preview"
            if "fast" in model_name.lower():
                # Veo 3 Fast - exclude duration_seconds (fixed at 8 seconds)
                config = types.GenerateVideosConfig(
                    number_of_videos=number_of_videos,
                    aspect_ratio=aspect_ratio,
                )
                print(f"📏 Using Veo 3 Fast with fixed 8-second duration")
            else:
                # Other models that support custom duration
                config = types.GenerateVideosConfig(
                    number_of_videos=number_of_videos,
                    aspect_ratio=aspect_ratio,
                    duration_seconds=duration_seconds,
                )
                print(f"📏 Using custom duration: {duration_seconds} seconds")
            
            operation = self.client.models.generate_videos(
                model=model_name,
                prompt=prompt,
                config=config
            )
            
            # Step 2: Wait for completion
            print(f"⏳ Waiting for video generation to complete...")
            while not operation.done:
                print("   Still generating...")
                time.sleep(5)  # Wait 5 seconds between checks
                operation = self.client.operations.get(operation)
            
            # Step 3: Extract video information
            if not operation.response:
                raise Exception("Video generation completed but no response received")
            
            generated_video = operation.response.generated_videos[0]
            video_uri = generated_video.video.uri
            video_id = str(uuid.uuid4())
            
            # Step 4: Handle video storage
            local_file_path = None
            s3_url = None
            
            if upload_to_s3 and aws_service:
                # Always download locally first, then upload to S3
                print(f"📥 Downloading video from Google to local filesystem...")
                
                # Create filename using just the video_id
                filename = f"{video_id}.mp4"
                filepath = os.path.join(self.downloads_dir, filename)
                
                # Download and save the video file
                with open(filepath, 'wb') as f:
                    video_data = self.client.files.download(file=generated_video.video)
                    f.write(video_data)
                
                local_file_path = filepath
                print(f"✅ Video downloaded to: {filepath}")
                
                # Now upload the local file to S3
                try:
                    print(f"☁️ Uploading local video file to S3...")
                    with open(filepath, 'rb') as f:
                        video_data = f.read()
                    
                    s3_url = aws_service.upload_video(video_data, video_id)
                    print(f"✅ Video uploaded to S3: {s3_url}")
                    
                    # Clean up local file after successful S3 upload
                    os.remove(filepath)
                    local_file_path = None
                    print(f"🗑️ Cleaned up local file: {filepath}")
                    
                except Exception as s3_error:
                    print(f"❌ Failed to upload local file to S3: {s3_error}")
                    # Keep local file as fallback
                    print(f"📁 Local file kept at: {filepath}")
            else:
                # Download to local filesystem only
                print(f"📥 Downloading video from Google to local filesystem...")
                
                # Create filename using just the video_id
                filename = f"{video_id}.mp4"
                filepath = os.path.join(self.downloads_dir, filename)
                
                # Download and save the video file
                with open(filepath, 'wb') as f:
                    video_data = self.client.files.download(file=generated_video.video)
                    f.write(video_data)
                
                local_file_path = filepath
                print(f"✅ Video saved to: {filepath}")
            
            # After S3 upload or local save, push embedding to Pinecone
            if pinecone_service is not None:
                pinecone_service.add_prompt_embedding(
                    prompt=prompt,
                    video_id=video_id,
                    s3_url=s3_url
                )

            return VideoGenerationResult(
                operation_id=operation_id,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                number_of_videos=number_of_videos,
                status="completed",
                created_at=time.time(),
                video_uri=video_uri,
                video_id=video_id,
                video_file=local_file_path or s3_url,  # Local path or S3 URL
                generation_complete=True,
                download_complete=True,
                s3_url=s3_url  # New field for S3 URL
            )
            
        except Exception as e:
            raise Exception(f"Failed to generate video: {str(e)}") 