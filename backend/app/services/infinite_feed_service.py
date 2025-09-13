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

class InfiniteFeedService:
    """Service for managing infinite video feeds using Redis and S3"""
    
    def __init__(self, redis_service: RedisService, aws_service: AWSService):
        self.redis_service = redis_service
        self.aws_service = aws_service
        self.target_feed_size = 200  # Keep 200 videos in queue
        self.refill_threshold = 50   # Refill when < 50 videos remain  
        self.videos_per_refill = 100  # Add 100 videos each refill
    
    def get_feed(self, request: FeedRequest) -> FeedResponse:
        """
        Get paginated video feed for a user - infinite scrolling
        
        Args:
            request: Feed request with user_id, cursor, limit, etc.
            
        Returns:
            FeedResponse with video list and pagination info
        """
        try:
            start_time = time.time()
            
            # Check if feed exists or needs initial generation
            current_feed_size = self.redis_service.get_feed_size(request.user_id)
            
            if request.refresh or current_feed_size == 0:
                logger.info(f"Initializing infinite feed for user {request.user_id}")
                generation_result = self._initialize_infinite_feed(request.user_id)
                if not generation_result.success:
                    return FeedResponse(
                        success=False,
                        videos=[],
                        total_videos=0,
                        cursor=request.cursor,
                        next_cursor=None,
                        has_more=False,
                        feed_size=0,
                        message=f"Failed to initialize feed: {generation_result.message}"
                    )
                current_feed_size = generation_result.total_feed_size
            
            # Check if we need to refill the queue (infinite scrolling logic)
            if current_feed_size < self.refill_threshold:
                logger.info(f"Refilling infinite feed for user {request.user_id} (current size: {current_feed_size})")
                self._refill_infinite_feed(request.user_id)
                current_feed_size = self.redis_service.get_feed_size(request.user_id)
            
            # Handle cursor that exceeds current queue size - refill and adjust cursor
            if request.cursor >= current_feed_size:
                logger.info(f"Cursor {request.cursor} exceeds feed size {current_feed_size}, refilling and adjusting")
                # Refill the queue
                self._refill_infinite_feed(request.user_id)
                current_feed_size = self.redis_service.get_feed_size(request.user_id)
                
                # If cursor still exceeds, we need to loop back or add more videos
                if request.cursor >= current_feed_size:
                    # For infinite scrolling, we can "wrap around" by using modulo
                    # Or we can add even more videos to the queue
                    additional_refills = (request.cursor // current_feed_size) + 1
                    for _ in range(additional_refills):
                        self._refill_infinite_feed(request.user_id)
                    current_feed_size = self.redis_service.get_feed_size(request.user_id)
            
            # Get video IDs from Redis feed
            video_ids = self.redis_service.get_feed_videos(
                user_id=request.user_id,
                start=request.cursor,
                count=request.limit,
                reverse=True  # Highest scored videos first
            )
            
            if not video_ids:
                # This should never happen with infinite feed, but just in case
                logger.warning(f"No videos found for user {request.user_id}, forcing refill")
                self._refill_infinite_feed(request.user_id)
                video_ids = self.redis_service.get_feed_videos(
                    user_id=request.user_id,
                    start=request.cursor,
                    count=request.limit,
                    reverse=True
                )
            
            # Convert video IDs to feed items with metadata
            feed_videos = self._hydrate_video_ids(video_ids, request.user_id)
            
            # Calculate pagination - ALWAYS has more for infinite feed
            next_cursor = request.cursor + len(feed_videos)
            has_more = True  # Infinite feed always has more!
            
            processing_time = time.time() - start_time
            
            return FeedResponse(
                success=True,
                videos=feed_videos,
                total_videos=len(feed_videos),
                cursor=request.cursor,
                next_cursor=next_cursor,
                has_more=has_more,  # Always True for infinite
                feed_size=current_feed_size,
                message=f"Infinite feed retrieved successfully in {processing_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to get infinite feed for user {request.user_id}: {str(e)}")
            return FeedResponse(
                success=False,
                videos=[],
                total_videos=0,
                cursor=request.cursor,
                next_cursor=None,
                has_more=True,  # Even on error, suggest there might be more
                feed_size=0,
                message=f"Failed to retrieve feed: {str(e)}"
            )
    
    def _initialize_infinite_feed(self, user_id: str) -> FeedGenerationResponse:
        """
        Initialize an infinite feed for a user
        
        Args:
            user_id: User to generate feed for
            
        Returns:
            FeedGenerationResponse with generation results
        """
        try:
            start_time = time.time()
            
            # Clear existing feed
            self.redis_service.clear_feed(user_id)
            
            # Get all available videos from S3
            all_videos = self.aws_service.list_videos(max_keys=1000)
            
            if not all_videos:
                return FeedGenerationResponse(
                    success=False,
                    user_id=user_id,
                    videos_added=0,
                    total_feed_size=0,
                    generation_time=time.time() - start_time,
                    message="No videos available in S3"
                )
            
            # Generate initial queue (repeat videos if necessary to reach target size)
            videos_added = self._populate_feed_queue(user_id, all_videos, self.target_feed_size)
            
            # Set feed expiry (24 hours)
            self.redis_service.set_feed_expiry(user_id, 24 * 3600)
            
            final_feed_size = self.redis_service.get_feed_size(user_id)
            generation_time = time.time() - start_time
            
            logger.info(f"Initialized infinite feed for user {user_id}: {videos_added} videos in {generation_time:.2f}s")
            
            return FeedGenerationResponse(
                success=True,
                user_id=user_id,
                videos_added=videos_added,
                total_feed_size=final_feed_size,
                generation_time=generation_time,
                message=f"Infinite feed initialized with {videos_added} videos"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize infinite feed for user {user_id}: {str(e)}")
            return FeedGenerationResponse(
                success=False,
                user_id=user_id,
                videos_added=0,
                total_feed_size=0,
                generation_time=time.time() - start_time,
                message=f"Feed initialization failed: {str(e)}"
            )
    
    def _refill_infinite_feed(self, user_id: str) -> bool:
        """
        Refill the infinite feed queue when it gets low
        
        Args:
            user_id: User to refill feed for
            
        Returns:
            True if refill was successful
        """
        try:
            # Get all available videos from S3
            all_videos = self.aws_service.list_videos(max_keys=1000)
            
            if not all_videos:
                logger.warning(f"No videos available for refill for user {user_id}")
                return False
            
            # Add more videos to the queue
            videos_added = self._populate_feed_queue(user_id, all_videos, self.videos_per_refill, append=True)
            
            logger.info(f"Refilled infinite feed for user {user_id}: added {videos_added} videos")
            return videos_added > 0
            
        except Exception as e:
            logger.error(f"Failed to refill infinite feed for user {user_id}: {str(e)}")
            return False
    
    def _populate_feed_queue(self, user_id: str, available_videos: List[VideoListItem], 
                           target_count: int, append: bool = False) -> int:
        """
        Populate the feed queue with videos, repeating videos if necessary
        
        Args:
            user_id: User to populate feed for
            available_videos: List of available videos from S3
            target_count: Number of videos to add
            append: Whether to append to existing queue or replace
            
        Returns:
            Number of videos actually added
        """
        if not available_videos:
            return 0
        
        videos_added = 0
        videos_to_add = []
        round_number = 0
        
        # Generate enough videos to reach target_count
        # Repeat and shuffle videos if we have fewer unique videos than target
        while len(videos_to_add) < target_count:
            # Shuffle the available videos for this round
            shuffled_videos = available_videos.copy()
            random.shuffle(shuffled_videos)
            
            for video in shuffled_videos:
                if len(videos_to_add) >= target_count:
                    break
                
                # Make video ID unique by adding round number and position
                # This allows the same video to appear multiple times in the queue
                unique_video_id = f"{video.video_id}:{round_number}:{len(videos_to_add)}"
                
                # Generate a random score with some variation to ensure uniqueness
                score = random.random() + (time.time() % 1000) / 10000 + round_number
                videos_to_add.append((unique_video_id, video.video_id, score))
            
            round_number += 1
        
        # Add videos to Redis feed
        for unique_video_id, original_video_id, score in videos_to_add:
            # Store mapping of unique_id -> original_id for later retrieval
            mapping_key = f"video_mapping:{user_id}:{unique_video_id}"
            self.redis_service.get_client().set(mapping_key, original_video_id, ex=24*3600)  # 24 hour expiry
            
            if self.redis_service.add_to_feed(user_id, unique_video_id, score):
                videos_added += 1
            else:
                logger.warning(f"Failed to add video {unique_video_id} to infinite feed for user {user_id}")
        
        return videos_added
    
    def _hydrate_video_ids(self, video_ids: List[str], user_id: str) -> List[FeedVideoItem]:
        """
        Convert video IDs to FeedVideoItem objects with metadata
        
        Args:
            video_ids: List of video IDs from Redis (may include unique suffixes)
            
        Returns:
            List of FeedVideoItem objects with metadata
        """
        feed_items = []
        
        for unique_video_id in video_ids:
            try:
                # Get the original video ID from the mapping
                if ':' in unique_video_id:
                    # This is a repeated video with unique suffix
                    mapping_key = f"video_mapping:{user_id}:{unique_video_id}"
                    original_video_id = self.redis_service.get_client().get(mapping_key)
                    if original_video_id:
                        video_id = original_video_id
                    else:
                        # Fallback: extract original video ID from unique ID
                        video_id = unique_video_id.split(':')[0]
                else:
                    video_id = unique_video_id
                
                # Get video info from AWS service using original video ID
                video_info = self.aws_service.get_video_by_id(video_id)
                
                if video_info:
                    # Create feed item from video info, but use unique_video_id for tracking
                    feed_item = FeedVideoItem(
                        video_id=unique_video_id,  # Use unique ID for frontend tracking
                        video_url=video_info.url,
                        thumbnail_url=None,
                        duration_seconds=video_info.metadata.duration_seconds if video_info.metadata else None,
                        aspect_ratio=video_info.metadata.aspect_ratio if video_info.metadata else None,
                        title=video_info.metadata.title if video_info.metadata else None,
                        description=video_info.metadata.description if video_info.metadata else None,
                        score=None,
                        size=video_info.content_length,
                        last_modified=video_info.last_modified
                    )
                    feed_items.append(feed_item)
                else:
                    logger.warning(f"Video {video_id} not found in S3, skipping")
                    
            except Exception as e:
                logger.error(f"Failed to hydrate video {unique_video_id}: {str(e)}")
                continue
        
        return feed_items
    
    def get_feed_stats(self, user_id: str) -> FeedStatsResponse:
        """Get statistics about a user's infinite feed"""
        try:
            feed_size = self.redis_service.get_feed_size(user_id)
            is_healthy = feed_size >= self.refill_threshold
            
            return FeedStatsResponse(
                user_id=user_id,
                feed_size=feed_size,
                videos_consumed=0,  # TODO: Implement consumption tracking
                last_refresh=None,  # TODO: Store refresh timestamps
                is_healthy=is_healthy
            )
        except Exception as e:
            logger.error(f"Failed to get infinite feed stats for user {user_id}: {str(e)}")
            return FeedStatsResponse(
                user_id=user_id,
                feed_size=0,
                videos_consumed=0,
                last_refresh=None,
                is_healthy=False
            ) 