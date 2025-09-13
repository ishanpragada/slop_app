from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List

class VideoMetadata(BaseModel):
    """Metadata for video files"""
    source: Optional[str] = Field(None, description="Source of the video (e.g., 'uploaded', 'ai_generated')")
    model: Optional[str] = Field(None, description="AI model used for generation (e.g., 'veo-3.0-fast-generate-preview')")
    google_operation_id: Optional[str] = Field(None, description="Google's operation ID for AI-generated videos")
    google_uri: Optional[str] = Field(None, description="Direct Google URI for the video")
    generation_type: Optional[str] = Field(None, description="Type of generation (e.g., 'text_to_video')")
    downloaded_at: Optional[str] = Field(None, description="Timestamp when video was downloaded")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    tags: Optional[List[str]] = Field(None, description="Video tags")
    user_id: Optional[str] = Field(None, description="ID of the user who uploaded/generated the video")
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds")
    aspect_ratio: Optional[str] = Field(None, description="Video aspect ratio (e.g., '16:9', '9:16')")
    has_audio: Optional[bool] = Field(None, description="Whether the video has audio")
    
    class Config:
        # Allow extra fields for flexibility
        extra = "allow"

class VideoInfo(BaseModel):
    """Complete video information including data and metadata"""
    video_id: str = Field(..., description="Unique video identifier")
    video_data: bytes = Field(..., description="Binary video data")
    content_type: str = Field(default="video/mp4", description="MIME type of the video")
    content_length: int = Field(..., description="Size of the video in bytes")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    url: str = Field(..., description="Public URL for the video")
    metadata: Optional[VideoMetadata] = Field(None, description="Video metadata")
    
    class Config:
        # Allow bytes type which isn't JSON serializable
        arbitrary_types_allowed = True

class VideoListItem(BaseModel):
    """Video information for listing (without video data)"""
    video_id: str = Field(..., description="Unique video identifier")
    url: str = Field(..., description="Public URL for the video")
    size: int = Field(..., description="Size of the video in bytes")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    metadata: Optional[VideoMetadata] = Field(None, description="Video metadata if available")

class VideoUploadResult(BaseModel):
    """Result of video upload operation"""
    success: bool = Field(..., description="Whether the upload was successful")
    video_id: str = Field(..., description="Unique video identifier")
    video_url: str = Field(..., description="Public URL for the uploaded video")
    metadata_url: Optional[str] = Field(None, description="URL for the metadata file if saved")
    message: str = Field(..., description="Success or error message")

class VideoExistsResult(BaseModel):
    """Result of video existence check"""
    video_id: str = Field(..., description="Video ID that was checked")
    exists: bool = Field(..., description="Whether the video exists")

class VideoListResult(BaseModel):
    """Result of video listing operation"""
    videos: List[VideoListItem] = Field(..., description="List of videos")
    count: int = Field(..., description="Number of videos returned")

class VideoMetadataResult(BaseModel):
    """Result of metadata save operation"""
    success: bool = Field(..., description="Whether the save was successful")
    video_id: str = Field(..., description="Video ID for which metadata was saved")
    metadata_url: str = Field(..., description="URL where metadata is stored")
    message: str = Field(..., description="Success or error message")

class VideoDeleteResult(BaseModel):
    """Result of video deletion operation"""
    success: bool = Field(..., description="Whether the deletion was successful")
    video_id: str = Field(..., description="Video ID that was deleted")
    message: str = Field(..., description="Success or error message") 