from pydantic import BaseModel, Field
from typing import Optional, Any

class VideoGenerationRequest(BaseModel):
    """Request model for AI video generation"""
    prompt: str = Field(..., description="Text description for video generation")
    aspect_ratio: Optional[str] = Field("16:9", description="Video aspect ratio")
    duration_seconds: Optional[int] = Field(8, description="Video duration in seconds (fixed at 8 for Veo 3 Fast)")
    number_of_videos: Optional[int] = Field(1, description="Number of videos to generate")

class VideoGenerationResult(BaseModel):
    """Result of complete video generation workflow"""
    operation_id: str = Field(..., description="Internal operation ID for tracking")
    prompt: str = Field(..., description="Text prompt used for generation")
    aspect_ratio: str = Field(..., description="Video aspect ratio")
    duration_seconds: int = Field(..., description="Video duration in seconds")
    number_of_videos: int = Field(..., description="Number of videos requested")
    status: str = Field(..., description="Current status of generation")
    created_at: float = Field(..., description="Unix timestamp when generation started")
    video_uri: Optional[str] = Field(None, description="Google video URI if complete")
    video_id: Optional[str] = Field(None, description="Generated video ID if complete")
    video_file: Optional[Any] = Field(None, description="Local file path or S3 URL")
    generation_complete: bool = Field(False, description="Whether generation is fully complete")
    download_complete: bool = Field(False, description="Whether download completed successfully")
    s3_url: Optional[str] = Field(None, description="S3 URL if uploaded to S3")
    
    class Config:
        # Allow arbitrary types for video file object
        arbitrary_types_allowed = True