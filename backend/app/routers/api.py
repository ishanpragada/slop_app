import uuid
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any, List
import io
import json
from app.services.aws_service import AWSService
from app.services.video_generation_service import VideoGenerationService
from app.services.prompt_generation_service import PromptGenerationService
from app.services.redis_service import RedisService
from app.services.feed_service import FeedService
from app.services.infinite_feed_service import InfiniteFeedService
from app.services.pinecone_service import PineconeService
from app.services.analytics_service import AnalyticsService
from app.services.user_preference_service import UserPreferenceService
from app.services.database_service import DatabaseService
from app.services.video_generation_queue_service import VideoGenerationQueueService
from app.services.worker_manager_service import WorkerManagerService
from dotenv import load_dotenv
from pydantic import BaseModel

router = APIRouter()
load_dotenv()
aws_service = AWSService()
video_gen_service = VideoGenerationService()
prompt_gen_service = PromptGenerationService()
redis_service = RedisService()
feed_service = FeedService(redis_service, aws_service)
infinite_feed_service = InfiniteFeedService(redis_service, aws_service)
pinecone_service = PineconeService()
analytics_service = AnalyticsService()
user_preference_service = UserPreferenceService()
database_service = DatabaseService()
video_queue_service = VideoGenerationQueueService()
worker_manager_service = WorkerManagerService()

# Import models from models package
from app.models.video_generation_models import VideoGenerationRequest
from app.models.prompt_models import PromptRequest, PromptResult
from app.models.feed_models import FeedRequest, FeedResponse, FeedGenerationRequest
from app.models.analytics_models import UserInteractionRequest, CommentRequest, AnalyticsResponse, VideoAnalytics, UserAnalytics

@router.get("/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}

@router.get("/redis/health")
async def redis_health():
    """Check Redis connection health"""
    try:
        is_connected = redis_service.is_connected()
        if is_connected:
            return {
                "status": "healthy",
                "redis_connected": True,
                "message": "Redis connection is working"
            }
        else:
            return {
                "status": "unhealthy", 
                "redis_connected": False,
                "message": "Redis connection failed"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis health check failed: {str(e)}")

@router.get("/feed")
async def get_video_feed(
    user_id: Optional[str] = "anonymous",
    cursor: Optional[int] = 0,
    limit: Optional[int] = 10,
    refresh: Optional[bool] = False
):
    """
    Get personalized video feed for a user
    
    Args:
        user_id: User ID for personalized feed (defaults to 'anonymous')
        cursor: Starting position for pagination (defaults to 0)
        limit: Number of videos to return (defaults to 10, max 50)
        refresh: Whether to refresh/regenerate the feed (defaults to False)
    """
    try:
        # Validate and limit parameters
        limit = min(limit, 50)  # Cap at 50 videos per request
        
        request = FeedRequest(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            refresh=refresh
        )
        
        response = feed_service.get_feed(request)
        
        # Display both queues after feed fetch - show from current cursor position
        redis_service.display_next_reels(user_id, count=5, start_position=cursor)
        redis_service.display_video_generation_queue(user_id, count=5)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video feed: {str(e)}")

@router.post("/feed/generate")
async def generate_video_feed(request: FeedGenerationRequest):
    """
    Generate a new video feed for a user
    
    Args:
        request: Feed generation parameters including user_id and feed_size
    """
    try:
        response = feed_service.generate_feed(
            user_id=request.user_id,
            feed_size=request.feed_size,
            force_refresh=request.force_refresh
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video feed: {str(e)}")

@router.get("/feed/stats/{user_id}")
async def get_feed_stats(user_id: str):
    """
    Get statistics about a user's feed
    
    Args:
        user_id: User ID to get stats for
    """
    try:
        stats = feed_service.get_feed_stats(user_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feed stats: {str(e)}")

@router.delete("/feed/{user_id}/video/{video_id}")
async def remove_video_from_feed(user_id: str, video_id: str):
    """
    Remove a specific video from user's feed
    
    Args:
        user_id: User ID
        video_id: Video ID to remove
    """
    try:
        success = feed_service.remove_video_from_feed(user_id, video_id)
        
        if success:
            return {
                "success": True,
                "message": f"Video {video_id} removed from feed for user {user_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to remove video {video_id} from feed for user {user_id}"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove video from feed: {str(e)}")

@router.get("/feed/infinite")
async def get_infinite_video_feed(
    user_id: Optional[str] = "anonymous",
    cursor: Optional[int] = 0,
    limit: Optional[int] = 10,
    refresh: Optional[bool] = False
):
    """
    Get infinite personalized video feed for a user - never ends!
    
    Args:
        user_id: User ID for personalized feed (defaults to 'anonymous')
        cursor: Starting position for pagination (defaults to 0)
        limit: Number of videos to return (defaults to 10, max 50)
        refresh: Whether to refresh/regenerate the feed (defaults to False)
    """
    try:
        # Validate and limit parameters
        limit = min(limit, 50)  # Cap at 50 videos per request
        
        request = FeedRequest(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            refresh=refresh
        )
        
        response = infinite_feed_service.get_feed(request)
        
        # Display both queues after infinite feed fetch - show from current cursor position
        redis_service.display_next_reels(user_id, count=5, start_position=cursor)
        redis_service.display_video_generation_queue(user_id, count=5)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get infinite video feed: {str(e)}")

@router.get("/feed/infinite/stats/{user_id}")
async def get_infinite_feed_stats(user_id: str):
    """
    Get statistics about a user's infinite feed
    
    Args:
        user_id: User ID to get stats for
    """
    try:
        stats = infinite_feed_service.get_feed_stats(user_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get infinite feed stats: {str(e)}")

@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    Upload a video to S3
    
    Args:
        file: Video file to upload
        metadata: Optional JSON string containing video metadata
    """
    try:
        # Read file content
        video_data = await file.read()
        
        # Always generate a unique video ID
        video_id = str(uuid.uuid4())
            
        # Upload video
        video_url = aws_service.upload_video(
            video_data=video_data,
            video_id=video_id,
            content_type=file.content_type or 'video/mp4'
        )
        
        return {
            "success": True,
            "video_id": video_id,
            "video_url": video_url,
            "message": "Video uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")

@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    Retrieve a specific video by ID
    
    Args:
        video_id: UUID string with or without .mp4 extension (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    """
    try:
        video_info = aws_service.get_video_by_id(video_id)
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Return video as streaming response
        video_stream = io.BytesIO(video_info.video_data)
        
        return StreamingResponse(
            video_stream,
            media_type=video_info.content_type,
            headers={
                "Content-Length": str(video_info.content_length),
                "Content-Disposition": f"attachment; filename={video_id}.mp4"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve video: {str(e)}")

@router.get("/videos/{video_id}/info")
async def get_video_info(video_id: str):
    """
    Get video information without downloading the actual video data
    
    Args:
        video_id: Video ID (with or without .mp4 extension)
    """
    try:
        video_info = aws_service.get_video_by_id(video_id)
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Return info without video data to save bandwidth
        return {
            "video_id": video_info.video_id,
            "content_type": video_info.content_type,
            "content_length": video_info.content_length,
            "last_modified": video_info.last_modified,
            "url": video_info.url,
            "metadata": video_info.metadata.dict() if video_info.metadata else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")

@router.get("/videos/{video_id}/url")
async def get_video_url(video_id: str):
    """
    Get the public URL for a video
    
    Args:
        video_id: Video ID (without .mp4 extension)
    """
    try:
        # Remove .mp4 extension if present
        video_id = video_id.replace('.mp4', '')
        url = aws_service.get_video_url(video_id)
        
        return {
            "video_id": video_id,
            "url": url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video URL: {str(e)}")

@router.get("/videos")
async def list_videos(prefix: str = "videos/", max_keys: int = 100):
    """
    List all videos in the S3 bucket
    
    Args:
        prefix: S3 key prefix to filter by
        max_keys: Maximum number of videos to return
    """
    try:
        videos = aws_service.list_videos(prefix=prefix, max_keys=max_keys)
        
        return {
            "videos": [video.dict() for video in videos],
            "count": len(videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")

@router.get("/videos/{video_id}/exists")
async def check_video_exists(video_id: str):
    """
    Check if a video exists in S3
    
    Args:
        video_id: Video ID (without .mp4 extension)
    """
    try:
        # Remove .mp4 extension if present
        video_id = video_id.replace('.mp4', '')
        exists = aws_service.video_exists(video_id)
        
        return {
            "video_id": video_id,
            "exists": exists
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check video existence: {str(e)}")

@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a video and its associated metadata
    
    Args:
        video_id: Video ID (without .mp4 extension)
    """
    try:
        # Remove .mp4 extension if present
        video_id = video_id.replace('.mp4', '')
        success = aws_service.delete_video(video_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Video not found or failed to delete")
        
        return {
            "success": True,
            "video_id": video_id,
            "message": "Video deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")

# ============================================================================
# AI VIDEO GENERATION ENDPOINTS
# ============================================================================

@router.post("/ai/videos/generate")
async def generate_ai_video_complete(
    request: VideoGenerationRequest
):
    """
    Complete AI video generation workflow - generates video and waits for completion
    
    Args:
        request: Video generation parameters
        
    Returns:
        Complete generation results including video URI
    """
    try:
        # TEMPORARY: Video generation disabled for testing
        pass  # TEMPORARY MODE: Video generation API disabled
        print(f"   Would have generated video with prompt: {request.prompt}")
        
        raise HTTPException(
            status_code=503, 
            detail="Video generation temporarily disabled for testing. Please try again later."
        )
        
        response = {
            "success": True,
            "operation_id": result.operation_id,
            "status": result.status,
            "video_uri": result.video_uri,
            "video_id": result.video_id,
            "generation_complete": result.generation_complete,
            "download_complete": result.download_complete,
            "completion_time": time.time(),
            "local_file_path": result.video_file if not result.s3_url else None,
            "s3_url": result.s3_url,
            "upload_method": "local_to_s3" if result.s3_url and not result.video_file else "local_only",
            "prompt": result.prompt,
            "settings": {
                "aspect_ratio": result.aspect_ratio,
                "duration_seconds": result.duration_seconds,
                "number_of_videos": result.number_of_videos
            },
            "created_at": result.created_at,
            "metadata": {
                "google_uri": result.video_uri,
                "generation_complete": True,
                "note": "Veo 3 Fast videos have fixed 8-second duration with audio generation"
            }
        }
        
        # Save metadata to PostgreSQL database
        postgres_save_result = None
        if result.s3_url and result.video_id:
            try:
                postgres_save_result = database_service.save_video_metadata(
                    video_id=result.video_id,
                    s3_url=result.s3_url,
                    prompt=request.prompt,
                    length_seconds=8,  # Veo 3 Fast has fixed 8-second duration
                    caption=None  # Can be enhanced later to generate auto-captions
                )
                
                response.update({
                    "saved_to_postgres": postgres_save_result.get("success", False),
                    "postgres_video_id": result.video_id
                })
                
                pass  # Video metadata saved to PostgreSQL
                
            except Exception as postgres_error:
                pass  # Failed to save to PostgreSQL
                response.update({
                    "saved_to_postgres": False,
                    "postgres_error": str(postgres_error)
                })
        
        
        response["message"] = "Video generation completed successfully"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")

@router.post("/ai/prompts/generate")
async def generate_prompt(request: PromptRequest):
    """
    Generate a random detailed prompt for Veo 3 Fast video generation
    
    Args:
        request: Prompt generation parameters
        
    Returns:
        Detailed prompt optimized for Veo 3 Fast
    """
    try:
        prompt_data = prompt_gen_service.generate_prompt_with_metadata(request.base_topic)
        
        result = PromptResult(
            prompt=prompt_data["prompt"],
            base_topic=prompt_data["base_topic"],
            style=prompt_data["style"],
            camera_movement=prompt_data["camera_movement"],
            lighting=prompt_data["lighting"],
            category=prompt_data["category"],
            generation_method=prompt_data["generation_method"]
        )
        
        return {
            "success": True,
            "prompt": result,
            "message": "Prompt generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.post("/analytics/interaction")
async def track_user_interaction(request: UserInteractionRequest):
    """
    Track a user interaction with a video
    
    Args:
        request: User interaction data
        
    Returns:
        Analytics response with interaction details
    """
    try:
        # Set timestamp if not provided
        if not request.timestamp:
            request.timestamp = datetime.now().isoformat()
        
        # Track the interaction
        result = analytics_service.track_interaction(
            user_id=request.user_id,
            video_id=request.video_id,
            action=request.action,
            metadata=request.metadata
        )
        
        if result["success"]:
            return AnalyticsResponse(
                success=True,
                message=result["message"],
                interaction_id=result["interaction_id"],
                timestamp=result["timestamp"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track interaction: {str(e)}")

@router.post("/analytics/comment")
async def add_video_comment(request: CommentRequest):
    """
    Add a comment to a video
    
    Args:
        request: Comment data
        
    Returns:
        Analytics response with comment details
    """
    try:
        # Set timestamp if not provided
        if not request.timestamp:
            request.timestamp = datetime.now().isoformat()
        
        # Add the comment
        result = analytics_service.add_comment(
            user_id=request.user_id,
            video_id=request.video_id,
            comment_text=request.comment_text
        )
        
        if result["success"]:
            return AnalyticsResponse(
                success=True,
                message=result["message"],
                interaction_id=result["comment_id"],
                timestamp=result["timestamp"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@router.get("/analytics/video/{video_id}")
async def get_video_analytics(video_id: str):
    """
    Get analytics for a specific video
    
    Args:
        video_id: Video identifier
        
    Returns:
        Video analytics data
    """
    try:
        analytics = analytics_service.get_video_analytics(video_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return VideoAnalytics(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video analytics: {str(e)}")

@router.get("/analytics/user/{user_id}")
async def get_user_analytics(user_id: str):
    """
    Get analytics for a specific user
    
    Args:
        user_id: User identifier
        
    Returns:
        User analytics data
    """
    try:
        analytics = analytics_service.get_user_analytics(user_id)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return UserAnalytics(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")

@router.get("/analytics/video/{video_id}/comments")
async def get_video_comments(video_id: str, limit: int = 50):
    """
    Get comments for a specific video
    
    Args:
        video_id: Video identifier
        limit: Maximum number of comments to return
        
    Returns:
        List of comments for the video
    """
    try:
        comments = analytics_service.get_video_comments(video_id, limit)
        
        return {
            "success": True,
            "video_id": video_id,
            "comments": comments,
            "total_comments": len(comments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video comments: {str(e)}")

@router.post("/user-preference/interaction")
async def track_user_preference_interaction(request: UserInteractionRequest):
    """
    Track a user interaction for preference learning
    
    Args:
        request: User interaction data with action types: like, view, skip
        
    Returns:
        User preference service response
    """
    try:
        # Validate interaction type
        valid_actions = ["like", "view", "skip"]
        if request.action not in valid_actions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        # Track the interaction using user preference service
        result = user_preference_service.store_user_interaction(
            user_id=request.user_id,
            video_id=request.video_id,
            interaction_type=request.action
        )
        
        if result["success"]:
            # Display both queues after user interaction
            redis_service.display_next_reels(request.user_id, count=5)
            redis_service.display_video_generation_queue(request.user_id, count=5)
            
            return {
                "success": True,
                "message": result["message"],
                "preference_updated": result.get("preference_updated", False),
                "interactions_since_update": result.get("interactions_since_update", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to track interaction"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track user preference interaction: {str(e)}")

@router.get("/user-preference/{user_id}")
async def get_user_preference(user_id: str):
    """
    Get user's current preference vector
    
    Args:
        user_id: User identifier
        
    Returns:
        User preference data
    """
    try:
        preference = user_preference_service.get_user_preference(user_id)
        
        if preference:
            return {
                "success": True,
                "preference": {
                    "user_id": preference.user_id,
                    "preference_embedding": preference.preference_embedding,
                    "window_size": preference.window_size,
                    "last_updated": preference.last_updated,
                    "interactions_since_update": preference.interactions_since_update
                }
            }
        else:
            return {
                "success": True,
                "preference": None,
                "message": "No preference data found for user"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user preference: {str(e)}")

@router.get("/user-preference/{user_id}/interactions")
async def get_user_interactions(user_id: str):
    """
    Get user's current interaction window
    
    Args:
        user_id: User identifier
        
    Returns:
        User interaction window data
    """
    try:
        interactions = user_preference_service.get_user_interactions(user_id)
        
        if interactions:
            return {
                "success": True,
                "interactions": {
                    "user_id": interactions.user_id,
                    "interactions": [
                        {
                            "video_id": interaction.video_id,
                            "embedding": interaction.embedding,
                            "type": interaction.type,
                            "weight": interaction.weight,
                            "timestamp": interaction.timestamp
                        } for interaction in interactions.interactions
                    ],
                    "last_updated": interactions.last_updated
                }
            }
        else:
            return {
                "success": True,
                "interactions": None,
                "message": "No interaction data found for user"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user interactions: {str(e)}")

@router.get("/user-preference/{user_id}/watched-videos")
async def get_user_watched_videos(user_id: str):
    """
    Get list of video IDs that a user has watched
    
    Args:
        user_id: User identifier
        
    Returns:
        List of watched video IDs
    """
    try:
        watched_videos = user_preference_service.get_watched_videos(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "watched_videos": watched_videos,
            "count": len(watched_videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get watched videos: {str(e)}")

@router.post("/user-preference/{user_id}/watched-videos/{video_id}")
async def add_watched_video(user_id: str, video_id: str):
    """
    Manually add a video to user's watched list (mainly for testing/admin)
    
    Args:
        user_id: User identifier
        video_id: Video identifier to mark as watched
        
    Returns:
        Operation result
    """
    try:
        success = user_preference_service.add_watched_video(user_id, video_id)
        
        if success:
            return {
                "success": True,
                "message": f"Video {video_id} added to watched list for user {user_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to add video {video_id} to watched list"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add watched video: {str(e)}")

@router.get("/user-preference/{user_id}/has-watched/{video_id}")
async def check_if_user_watched_video(user_id: str, video_id: str):
    """
    Check if a user has watched a specific video
    
    Args:
        user_id: User identifier
        video_id: Video identifier to check
        
    Returns:
        Boolean indicating if video was watched
    """
    try:
        has_watched = user_preference_service.has_watched_video(user_id, video_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "video_id": video_id,
            "has_watched": has_watched
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check watched video: {str(e)}")

@router.delete("/user-preference/{user_id}/watched-videos/{video_id}")
async def remove_watched_video(user_id: str, video_id: str):
    """
    Remove a video from user's watched list (mainly for testing/admin)
    
    Args:
        user_id: User identifier
        video_id: Video identifier to remove from watched list
        
    Returns:
        Operation result
    """
    try:
        success = user_preference_service.remove_watched_video(user_id, video_id)
        
        if success:
            return {
                "success": True,
                "message": f"Video {video_id} removed from watched list for user {user_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to remove video {video_id} from watched list"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove watched video: {str(e)}")

# ============================================================================
# VIDEO GENERATION QUEUE ENDPOINTS
# ============================================================================

@router.get("/video-queue/{user_id}/status")
async def get_video_queue_status(user_id: str):
    """
    Get the current status of a user's video generation queue
    
    Args:
        user_id: User identifier
        
    Returns:
        Queue status and items
    """
    try:
        status = video_queue_service.get_user_queue_status(user_id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video queue status: {str(e)}")

@router.post("/video-queue/{user_id}/process")
async def process_user_preference_vector(user_id: str):
    """
    Manually trigger video queue processing for a user's current preference vector
    (mainly for testing/admin purposes)
    
    Args:
        user_id: User identifier
        
    Returns:
        Processing results
    """
    try:
        # Get user's current preference vector
        preference = user_preference_service.get_user_preference(user_id)
        
        if not preference or not preference.preference_embedding:
            raise HTTPException(
                status_code=404, 
                detail=f"No preference vector found for user {user_id}"
            )
        
        # Process the preference vector
        result = video_queue_service.process_new_preference_vector(
            user_id, 
            preference.preference_embedding
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process preference vector: {str(e)}")

# ============================================================================
# BACKGROUND WORKER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/workers/status")
async def get_worker_status():
    """
    Get status of all background video workers
    
    Returns:
        Worker status and statistics
    """
    try:
        status = worker_manager_service.get_worker_status()
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")

@router.get("/workers/health")
async def get_system_health():
    """
    Get overall system health for video generation
    
    Returns:
        System health status and component status
    """
    try:
        health = worker_manager_service.get_system_health()
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@router.get("/workers/queue-stats")
async def get_queue_statistics():
    """
    Get statistics about all video generation queues
    
    Returns:
        Queue statistics and details
    """
    try:
        stats = worker_manager_service.get_queue_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue statistics: {str(e)}")

@router.post("/workers/start")
async def start_background_worker(background: bool = True):
    """
    Start a new background video worker
    
    Args:
        background: Whether to start worker in background (default: True)
        
    Returns:
        Worker start result
    """
    try:
        result = worker_manager_service.start_worker(background=background)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start worker: {str(e)}")

@router.post("/workers/clear-stale")
async def clear_stale_workers():
    """
    Clear worker registrations that are no longer active
    
    Returns:
        Cleanup results
    """
    try:
        result = worker_manager_service.clear_stale_workers()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear stale workers: {str(e)}")

@router.post("/workers/process-all-pending")
async def process_all_pending_tasks():
    """
    Process all pending video generation tasks until queues are empty
    (This is a synchronous operation that may take a while)
    
    Returns:
        Processing results
    """
    try:
        from app.services.background_video_worker import BackgroundVideoWorker
        from datetime import datetime
        
        # Create a temporary worker for processing
        worker = BackgroundVideoWorker()
        worker.running = True
        worker.stats["started_at"] = datetime.now().isoformat()
        
        # Process all pending tasks
        total_processed = worker.process_all_pending_tasks()
        
        return {
            "success": True,
            "tasks_processed": total_processed,
            "message": f"Successfully processed {total_processed} video generation tasks",
            "completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process pending tasks: {str(e)}")

@router.post("/workers/process-single-task")
async def process_single_video_task(user_id: str = None):
    """
    Process a single video generation task from the queue
    
    Args:
        user_id: Optional user ID to process task for (if not provided, processes for any user)
    
    Returns:
        Task processing result
    """
    try:
        from app.services.background_video_worker import BackgroundVideoWorker
        from datetime import datetime
        
        worker = BackgroundVideoWorker()
        
        # If no user_id provided, find a user with pending tasks
        if not user_id:
            users_with_tasks = worker._get_all_users_with_pending_tasks()
            if not users_with_tasks:
                return {
                    "success": False,
                    "message": "No users with pending video generation tasks found"
                }
            user_id = users_with_tasks[0]
        
        # Get next task for the user
        task = worker.queue_service.get_next_generation_task(user_id)
        
        if not task or task.get("type") != "generate_video":
            return {
                "success": False,
                "message": f"No video generation tasks found for user {user_id}"
            }
        
        # Process the task
        success = worker._generate_video_for_task(user_id, task)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully generated video for user {user_id}",
                "task_prompt": task.get("prompt", ""),
                "processed_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to generate video for user {user_id}",
                "task_prompt": task.get("prompt", "")
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process video task: {str(e)}")

@router.get("/workers/logs")
async def get_worker_logs(lines: int = 50):
    """
    Get recent worker logs
    
    Args:
        lines: Number of log lines to return (default: 50)
        
    Returns:
        Recent worker logs
    """
    try:
        logs = worker_manager_service.get_worker_logs(lines=lines)
        return logs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker logs: {str(e)}")

# ============================================================================
# POSTGRESQL VIDEO DATABASE ENDPOINTS
# ============================================================================

@router.get("/videos/db/{video_id}")
async def get_video_from_database(video_id: str):
    """
    Get video metadata from PostgreSQL database by video_id
    
    Args:
        video_id: Video identifier
        
    Returns:
        Video metadata from PostgreSQL
    """
    try:
        video_data = database_service.get_video_by_id(video_id)
        
        if video_data:
            return {
                "success": True,
                "video": video_data,
                "message": "Video found in database"
            }
        else:
            raise HTTPException(status_code=404, detail="Video not found in database")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video from database: {str(e)}")

@router.get("/videos/db")
async def list_videos_from_database(
    limit: int = 50,
    offset: int = 0
):
    """
    List videos from PostgreSQL database with pagination
    
    Args:
        limit: Maximum number of videos to return (default: 50)
        offset: Number of videos to skip (default: 0)
        
    Returns:
        List of videos from PostgreSQL with pagination info
    """
    try:
        result = database_service.list_videos(limit=limit, offset=offset)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Failed to list videos"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos from database: {str(e)}")

@router.put("/videos/db/{video_id}/stats")
async def update_video_stats(
    video_id: str,
    like_count_increment: int = 0,
    share_count_increment: int = 0
):
    """
    Update video statistics in PostgreSQL database
    
    Args:
        video_id: Video identifier
        like_count_increment: Amount to increment like count by (default: 0)
        share_count_increment: Amount to increment share count by (default: 0)
        
    Returns:
        Update result
    """
    try:
        result = database_service.update_video_stats(
            video_id=video_id,
            like_count_increment=like_count_increment,
            share_count_increment=share_count_increment
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("message", "Video not found"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update video stats: {str(e)}")
