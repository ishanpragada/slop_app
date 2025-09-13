from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.aws_models import VideoMetadata

class FeedRequest(BaseModel):
    """Request model for getting video feed"""
    user_id: Optional[str] = Field("anonymous", description="User ID for personalized feed")
    cursor: Optional[int] = Field(0, description="Starting position for pagination")
    limit: Optional[int] = Field(10, description="Number of videos to return")
    refresh: Optional[bool] = Field(False, description="Whether to refresh/regenerate the feed")

class FeedVideoItem(BaseModel):
    """Simplified video item for feed responses"""
    video_id: str = Field(..., description="Unique video identifier")
    video_url: str = Field(..., description="Public URL for the video")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL if available")
    duration_seconds: Optional[int] = Field(None, description="Video duration in seconds")
    aspect_ratio: Optional[str] = Field(None, description="Video aspect ratio")
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    score: Optional[float] = Field(None, description="Feed ranking score")
    size: Optional[int] = Field(None, description="Video file size in bytes")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")

class FeedResponse(BaseModel):
    """Response model for video feed"""
    success: bool = Field(..., description="Whether the request was successful")
    videos: List[FeedVideoItem] = Field(..., description="List of videos in the feed")
    total_videos: int = Field(..., description="Total number of videos returned")
    cursor: int = Field(..., description="Current cursor position")
    next_cursor: Optional[int] = Field(None, description="Next cursor for pagination")
    has_more: bool = Field(..., description="Whether there are more videos available")
    feed_size: int = Field(..., description="Total size of user's feed queue")
    message: str = Field(..., description="Response message")

class FeedGenerationRequest(BaseModel):
    """Request for generating a new feed"""
    user_id: str = Field(..., description="User ID to generate feed for")
    feed_size: Optional[int] = Field(50, description="Number of videos to include in feed")
    force_refresh: Optional[bool] = Field(False, description="Force regeneration even if feed exists")

class FeedGenerationResponse(BaseModel):
    """Response for feed generation"""
    success: bool = Field(..., description="Whether generation was successful")
    user_id: str = Field(..., description="User ID the feed was generated for")
    videos_added: int = Field(..., description="Number of videos added to feed")
    total_feed_size: int = Field(..., description="Total size of the generated feed")
    generation_time: float = Field(..., description="Time taken to generate feed in seconds")
    message: str = Field(..., description="Generation result message")

class FeedStatsResponse(BaseModel):
    """Response model for feed statistics"""
    user_id: str = Field(..., description="User ID")
    feed_size: int = Field(..., description="Current feed size")
    videos_consumed: int = Field(..., description="Number of videos consumed/viewed")
    last_refresh: Optional[datetime] = Field(None, description="Last time feed was refreshed")
    is_healthy: bool = Field(..., description="Whether feed has enough videos") 