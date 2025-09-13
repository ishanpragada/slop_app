import random
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.redis_service import RedisService
from app.services.aws_service import AWSService
from app.models.feed_models import (
    FeedResponse, FeedVideoItem, FeedGenerationResponse, 
    FeedStatsResponse, FeedRequest
)
from app.models.aws_models import VideoListItem

logger = logging.getLogger(__name__)

class FeedService:
    """Service for managing video feeds using Redis and S3"""
    
    def __init__(self, redis_service: RedisService, aws_service: AWSService):
        self.redis_service = redis_service
        self.aws_service = aws_service
        self.default_feed_size = 50
        self.min_feed_threshold = 10  # Regenerate when feed has fewer than this many videos
    
    def get_feed(self, request: FeedRequest) -> FeedResponse:
        """
        Get paginated video feed for a user
        
        Args:
            request: Feed request with user_id, cursor, limit, etc.
            
        Returns:
            FeedResponse with video list and pagination info
        """
        try:
            start_time = time.time()
            
            # Check if feed exists or needs refresh
            current_feed_size = self.redis_service.get_feed_size(request.user_id)
            
            if request.refresh or current_feed_size < self.min_feed_threshold:
                logger.info(f"Generating new feed for user {request.user_id} (current size: {current_feed_size})")
                generation_result = self.generate_feed(request.user_id, self.default_feed_size)
                if not generation_result.success:
                    return FeedResponse(
                        success=False,
                        videos=[],
                        total_videos=0,
                        cursor=request.cursor,
                        next_cursor=None,
                        has_more=False,
                        feed_size=0,
                        message=f"Failed to generate feed: {generation_result.message}"
                    )
                current_feed_size = generation_result.total_feed_size
            
            # Get video IDs from Redis feed
            video_ids = self.redis_service.get_feed_videos(
                user_id=request.user_id,
                start=request.cursor,
                count=request.limit,
                reverse=True  # Highest scored videos first
            )
            
            if not video_ids:
                return FeedResponse(
                    success=True,
                    videos=[],
                    total_videos=0,
                    cursor=request.cursor,
                    next_cursor=None,
                    has_more=False,
                    feed_size=current_feed_size,
                    message="No videos available in feed"
                )
            
            # Convert video IDs to feed items with metadata
            feed_videos = self._hydrate_video_ids(video_ids)
            
            # Calculate pagination
            next_cursor = request.cursor + len(feed_videos) if len(feed_videos) == request.limit else None
            has_more = next_cursor is not None and next_cursor < current_feed_size
            
            processing_time = time.time() - start_time
            
            return FeedResponse(
                success=True,
                videos=feed_videos,
                total_videos=len(feed_videos),
                cursor=request.cursor,
                next_cursor=next_cursor,
                has_more=has_more,
                feed_size=current_feed_size,
                message=f"Feed retrieved successfully in {processing_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to get feed for user {request.user_id}: {str(e)}")
            return FeedResponse(
                success=False,
                videos=[],
                total_videos=0,
                cursor=request.cursor,
                next_cursor=None,
                has_more=False,
                feed_size=0,
                message=f"Failed to retrieve feed: {str(e)}"
            )
    
    def generate_feed(self, user_id: str, feed_size: int = 50, force_refresh: bool = False) -> FeedGenerationResponse:
        """
        Generate a new randomized feed for a user from available S3 videos
        
        Args:
            user_id: User to generate feed for
            feed_size: Number of videos to include in feed
            force_refresh: Whether to regenerate even if feed exists
            
        Returns:
            FeedGenerationResponse with generation results
        """
        try:
            start_time = time.time()
            
            # Check if feed already exists
            if not force_refresh:
                existing_size = self.redis_service.get_feed_size(user_id)
                if existing_size >= self.min_feed_threshold:
                    return FeedGenerationResponse(
                        success=True,
                        user_id=user_id,
                        videos_added=0,
                        total_feed_size=existing_size,
                        generation_time=time.time() - start_time,
                        message=f"Feed already exists with {existing_size} videos"
                    )
            
            # Clear existing feed
            self.redis_service.clear_feed(user_id)
            
            # Get all available videos from S3
            all_videos = self.aws_service.list_videos(max_keys=1000)  # Get up to 1000 videos
            
            if not all_videos:
                return FeedGenerationResponse(
                    success=False,
                    user_id=user_id,
                    videos_added=0,
                    total_feed_size=0,
                    generation_time=time.time() - start_time,
                    message="No videos available in S3"
                )
            
            # Generate random scores and shuffle videos
            scored_videos = []
            for video in all_videos:
                # Random score between 0.0 and 1.0 (higher is better)
                score = random.random()
                scored_videos.append((video.video_id, score))
            
            # Sort by score descending (best videos first)
            scored_videos.sort(key=lambda x: x[1], reverse=True)
            
            # Take the requested number of videos
            videos_to_add = scored_videos[:feed_size]
            
            # Add videos to Redis feed
            videos_added = 0
            for video_id, score in videos_to_add:
                if self.redis_service.add_to_feed(user_id, video_id, score):
                    videos_added += 1
                else:
                    logger.warning(f"Failed to add video {video_id} to feed for user {user_id}")
            
            # Set feed expiry (24 hours)
            self.redis_service.set_feed_expiry(user_id, 24 * 3600)
            
            final_feed_size = self.redis_service.get_feed_size(user_id)
            generation_time = time.time() - start_time
            
            logger.info(f"Generated feed for user {user_id}: {videos_added} videos in {generation_time:.2f}s")
            
            return FeedGenerationResponse(
                success=True,
                user_id=user_id,
                videos_added=videos_added,
                total_feed_size=final_feed_size,
                generation_time=generation_time,
                message=f"Feed generated successfully with {videos_added} videos"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate feed for user {user_id}: {str(e)}")
            return FeedGenerationResponse(
                success=False,
                user_id=user_id,
                videos_added=0,
                total_feed_size=0,
                generation_time=time.time() - start_time,
                message=f"Feed generation failed: {str(e)}"
            )
    
    def get_feed_stats(self, user_id: str) -> FeedStatsResponse:
        """Get statistics about a user's feed"""
        try:
            feed_size = self.redis_service.get_feed_size(user_id)
            is_healthy = feed_size >= self.min_feed_threshold
            
            return FeedStatsResponse(
                user_id=user_id,
                feed_size=feed_size,
                videos_consumed=0,  # TODO: Implement consumption tracking
                last_refresh=None,  # TODO: Store refresh timestamps
                is_healthy=is_healthy
            )
        except Exception as e:
            logger.error(f"Failed to get feed stats for user {user_id}: {str(e)}")
            return FeedStatsResponse(
                user_id=user_id,
                feed_size=0,
                videos_consumed=0,
                last_refresh=None,
                is_healthy=False
            )
    
    def remove_video_from_feed(self, user_id: str, video_id: str) -> bool:
        """Remove a specific video from user's feed (e.g., after viewing)"""
        try:
            return self.redis_service.remove_from_feed(user_id, video_id)
        except Exception as e:
            logger.error(f"Failed to remove video {video_id} from feed for user {user_id}: {str(e)}")
            return False
    
    def _hydrate_video_ids(self, video_ids: List[str]) -> List[FeedVideoItem]:
        """
        Convert video IDs to FeedVideoItem objects with metadata
        
        Args:
            video_ids: List of video IDs from Redis
            
        Returns:
            List of FeedVideoItem objects with metadata
        """
        feed_items = []
        
        for video_id in video_ids:
            try:
                # Get video info from AWS service
                video_info = self.aws_service.get_video_by_id(video_id)
                
                if video_info:
                    # Create feed item from video info
                    feed_item = FeedVideoItem(
                        video_id=video_info.video_id,
                        video_url=video_info.url,
                        thumbnail_url=None,  # TODO: Add thumbnail support
                        duration_seconds=video_info.metadata.duration_seconds if video_info.metadata else None,
                        aspect_ratio=video_info.metadata.aspect_ratio if video_info.metadata else None,
                        title=video_info.metadata.title if video_info.metadata else None,
                        description=video_info.metadata.description if video_info.metadata else None,
                        score=None,  # Could get this from Redis if needed
                        size=video_info.content_length,
                        last_modified=video_info.last_modified
                    )
                    feed_items.append(feed_item)
                else:
                    logger.warning(f"Video {video_id} not found in S3, skipping")
                    
            except Exception as e:
                logger.error(f"Failed to hydrate video {video_id}: {str(e)}")
                continue
        
        return feed_items 