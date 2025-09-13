# backend/app/services/aws_service.py
import os
import boto3
import json
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from app.models.aws_models import (
    VideoInfo, VideoListItem, VideoMetadata, VideoUploadResult,
    VideoExistsResult, VideoListResult, VideoMetadataResult, VideoDeleteResult
)

load_dotenv()

class AWSService:
    """AWS service integration for real AWS S3"""
    
    def __init__(self):
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Bucket names from environment
        self.videos_bucket = os.getenv('VIDEOS_BUCKET_NAME', 'slop-videos')
        
        # Initialize S3 client
        self.s3_client = self._create_s3_client()
        
    def _create_s3_client(self):
        """Create S3 client for AWS"""
        config = {
            'region_name': self.region,
        }
        
        # Use AWS credentials from environment or AWS CLI configuration
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        if aws_access_key_id and aws_secret_access_key:
            config.update({
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key,
            })
            
        return boto3.client('s3', **config)
    
    def upload_video(self, video_data: bytes, video_id: str, content_type: str = 'video/mp4') -> str:
        """
        Upload video to S3 and return the URL
        
        Args:
            video_data: Binary video data
            video_id: Unique identifier for the video
            content_type: MIME type of the video
            
        Returns:
            URL of the uploaded video
        """
        try:
            key = f"videos/{video_id}.mp4"
            
            self.s3_client.put_object(
                Bucket=self.videos_bucket,
                Key=key,
                Body=video_data,
                ContentType=content_type
                # Note: Public access should be configured at bucket level, not object level
            )
            
            # Generate URL
            url = f"https://{self.videos_bucket}.s3.{self.region}.amazonaws.com/{key}"
            print("IM HERE, ", url)
                
            print(f"✅ Video uploaded successfully: {url}")
            return url
            
        except ClientError as e:
            print(f"❌ Failed to upload video: {e}")
            raise
    
    def get_video_by_id(self, video_id: str) -> Optional[VideoInfo]:
        """
        Retrieve a specific video from S3 by its ID
        
        Args:
            video_id: UUID string with or without .mp4 extension (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
            
        Returns:
            VideoInfo object containing video data and metadata, or None if not found
        """
        try:
            # Ensure video_id ends with .mp4
            if not video_id.endswith('.mp4'):
                video_id = f"{video_id}.mp4"
            
            key = f"videos/{video_id}"
            
            # Get video object
            response = self.s3_client.get_object(
                Bucket=self.videos_bucket,
                Key=key
            )
            
            video_data = response['Body'].read()
            content_type = response.get('ContentType', 'video/mp4')
            content_length = response.get('ContentLength', 0)
            last_modified = response.get('LastModified')
            
            return VideoInfo(
                video_id=video_id.replace('.mp4', ''),
                video_data=video_data,
                content_type=content_type,
                content_length=content_length,
                last_modified=last_modified,
                url=self.get_video_url(video_id.replace('.mp4', '')),
                metadata=None
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"❌ Video {video_id} not found")
                return None
            else:
                print(f"❌ Failed to retrieve video {video_id}: {e}")
                raise
    
    def get_video_url(self, video_id: str) -> str:
        """Get the public URL for a video"""
        key = f"videos/{video_id}.mp4"
        return f"https://{self.videos_bucket}.s3.{self.region}.amazonaws.com/{key}"
    
    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in S3"""
        try:
            key = f"videos/{video_id}.mp4"
            self.s3_client.head_object(Bucket=self.videos_bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def list_videos(self, prefix: str = "videos/", max_keys: int = 100) -> List[VideoListItem]:
        """List videos in the S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.videos_bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            videos = []
            for obj in response.get('Contents', []):
                video_id = obj['Key'].replace('videos/', '').replace('.mp4', '')
                
                videos.append(VideoListItem(
                    video_id=video_id,
                    url=self.get_video_url(video_id),
                    size=obj['Size'],
                    last_modified=obj['LastModified'],
                    metadata=None
                ))
            
            return videos
            
        except ClientError as e:
            print(f"❌ Failed to list videos: {e}")
            return []
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video"""
        try:
            # Delete video
            self.s3_client.delete_object(
                Bucket=self.videos_bucket,
                Key=f"videos/{video_id}.mp4"
            )
            
            print(f"✅ Video {video_id} deleted successfully")
            return True
            
        except ClientError as e:
            print(f"❌ Failed to delete video {video_id}: {e}")
            return False 