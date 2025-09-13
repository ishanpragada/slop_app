from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class UserInteractionRequest(BaseModel):
    """Request model for user interaction analytics"""
    user_id: str = Field(..., description="Unique user identifier")
    video_id: str = Field(..., description="Video identifier")
    action: str = Field(..., description="Type of interaction: like, comment, share, save, view")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of the interaction")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional interaction metadata")

class CommentRequest(BaseModel):
    """Request model for video comments"""
    user_id: str = Field(..., description="Unique user identifier")
    video_id: str = Field(..., description="Video identifier")
    comment_text: str = Field(..., description="Comment content", max_length=1000)
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of the comment")

class AnalyticsResponse(BaseModel):
    """Response model for analytics operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    interaction_id: Optional[str] = Field(default=None, description="Unique interaction identifier")
    timestamp: str = Field(..., description="ISO timestamp of the operation")

class VideoAnalytics(BaseModel):
    """Model for video analytics summary"""
    video_id: str = Field(..., description="Video identifier")
    total_views: int = Field(default=0, description="Total number of views")
    total_likes: int = Field(default=0, description="Total number of likes")
    total_shares: int = Field(default=0, description="Total number of shares")
    total_saves: int = Field(default=0, description="Total number of saves")
    total_comments: int = Field(default=0, description="Total number of comments")
    average_watch_time: Optional[float] = Field(default=None, description="Average watch time in seconds")
    engagement_rate: Optional[float] = Field(default=None, description="Engagement rate as percentage")

class UserAnalytics(BaseModel):
    """Model for user analytics summary"""
    user_id: str = Field(..., description="User identifier")
    total_interactions: int = Field(default=0, description="Total number of interactions")
    videos_liked: int = Field(default=0, description="Number of videos liked")
    videos_commented: int = Field(default=0, description="Number of videos commented on")
    videos_shared: int = Field(default=0, description="Number of videos shared")
    videos_saved: int = Field(default=0, description="Number of videos saved")
    average_watch_time: Optional[float] = Field(default=None, description="Average watch time in seconds")

class UserInteraction(BaseModel):
    """Model for individual user interaction"""
    video_id: str = Field(..., description="Video identifier")
    embedding: List[float] = Field(..., description="Video embedding vector")
    type: str = Field(..., description="Type of interaction")
    weight: float = Field(..., description="Weight of the interaction")
    timestamp: str = Field(..., description="ISO timestamp of the interaction")

class UserInteractionWindow(BaseModel):
    """Model for user interaction window"""
    user_id: str = Field(..., description="User identifier")
    interactions: List[UserInteraction] = Field(..., description="List of interactions in the window")
    last_updated: str = Field(..., description="ISO timestamp of last update")

class UserPreference(BaseModel):
    """Model for user preference data"""
    user_id: str = Field(..., description="User identifier")
    preference_embedding: List[float] = Field(..., description="User preference vector")
    window_size: int = Field(default=20, description="Size of interaction window")
    last_updated: str = Field(..., description="ISO timestamp of last update")
    interactions_since_update: int = Field(default=0, description="Number of interactions since last update") 