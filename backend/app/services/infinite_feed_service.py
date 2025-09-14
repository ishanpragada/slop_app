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
        self.target_feed_size = 10  # Keep exactly 10 videos in queue
        self.refill_threshold = 2   # Refill when 2 videos remain (trigger preference update)
        self.videos_per_refill = 10  # Add 10 videos each refill
    
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
            
            print(f"\n🎬 INFINITE FEED REQUEST for user {request.user_id}")
            print(f"📊 Current feed size: {current_feed_size}")
            print(f"📍 User cursor position: {request.cursor}")
            print(f"🎯 Requesting {request.limit} videos")
            print(f"🔄 Refresh requested: {request.refresh}")
            
            # Calculate how many videos remain after this request
            videos_remaining_after_request = max(0, current_feed_size - (request.cursor + request.limit))
            print(f"📱 Videos remaining after this request: {videos_remaining_after_request}")
            print(f"⚠️  Will trigger refill if remaining < {self.refill_threshold}")
            print("=" * 60)
            
            if request.refresh or current_feed_size == 0:
                print(f"🔄 REFRESH TRIGGERED: Clearing existing feed and regenerating")
                print(f"📊 Current feed size before refresh: {current_feed_size}")
                
                # Manually clear the feed to ensure clean state
                print("🧹 Manually clearing feed before initialization...")
                self.redis_service.clear_feed(request.user_id)
                cleared_size = self.redis_service.get_feed_size(request.user_id)
                print(f"✅ Feed cleared, size now: {cleared_size}")
                
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
            
            # Check remaining videos after this request would be served
            remaining_after_request = current_feed_size - (request.cursor + request.limit)
            
            # Trigger refill when user is approaching the end (when they would have <= 2 videos left)
            if remaining_after_request <= self.refill_threshold:
                print(f"🚨 REFILL TRIGGERED: User will have {remaining_after_request} videos remaining after this request")
                print(f"🎯 Triggering preference update for user {request.user_id}")
                
                # Trigger preference update when feed is running low
                self._trigger_preference_update_if_needed(request.user_id)
                
                print(f"🔄 Refilling infinite feed to maintain seamless experience")
                refill_success = self._refill_infinite_feed(request.user_id)
                current_feed_size = self.redis_service.get_feed_size(request.user_id)
                
                print(f"✅ Refill completed: {refill_success}, new feed size: {current_feed_size}")
            
            # Handle cursor that exceeds current queue size - smart pagination approach
            if request.cursor >= current_feed_size:
                print(f"🚨 CURSOR OVERFLOW: User cursor ({request.cursor}) >= feed size ({current_feed_size})")
                print(f"🎯 Triggering preference update and feed rebuild for cursor overflow")
                
                # Trigger preference update when feed is running low
                self._trigger_preference_update_if_needed(request.user_id)
                
                print(f"🔄 Smart refill: rebuilding feed with updated preferences")
                # Refill the queue (this clears and rebuilds with exactly 10 videos)
                refill_success = self._refill_infinite_feed(request.user_id)
                current_feed_size = self.redis_service.get_feed_size(request.user_id)
                
                print(f"✅ Smart refill completed: {refill_success}, new feed size: {current_feed_size}")
                
                # Adjust cursor to reasonable position in new feed
                if request.cursor >= current_feed_size:
                    # Reset cursor to beginning of refreshed feed for seamless continuation
                    print(f"🔄 Resetting cursor from {request.cursor} to 0 for refreshed feed")
                    request.cursor = 0
            
            # Get video IDs from Redis feed
            video_ids = self.redis_service.get_feed_videos(
                user_id=request.user_id,
                start=request.cursor,
                count=request.limit,
                reverse=True  # Highest scored videos first
            )
            
            if not video_ids:
                # This should never happen with infinite feed, but just in case
                pass  # No videos found for user, forcing refill
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
            
            # Final status logging
            print(f"\n📋 FEED REQUEST COMPLETED")
            print(f"✅ Returned {len(feed_videos)} videos")
            print(f"📍 Next cursor: {next_cursor}")
            print(f"📊 Total feed size: {current_feed_size}")
            print(f"⏱️  Processing time: {processing_time:.3f}s")
            print(f"🔄 User progress: {request.cursor + len(feed_videos)}/{current_feed_size} videos consumed")
            
            remaining_videos = current_feed_size - (request.cursor + len(feed_videos))
            print(f"📱 Videos remaining in feed: {remaining_videos}")
            
            if remaining_videos <= 2:
                print(f"⚠️  USER IS NEAR END OF FEED! Next request will trigger refill.")
            
            print("=" * 60)
            
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
            pass  # Failed to get infinite feed for user
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
            
            print(f"\n🏗️  INITIALIZING INFINITE FEED")
            print(f"👤 User: {user_id}")
            print(f"🎯 Target feed size: {self.target_feed_size}")
            
            # Clear existing feed
            print("🧹 Clearing any existing feed data...")
            current_size_before = self.redis_service.get_feed_size(user_id)
            print(f"📊 Feed size before clear: {current_size_before}")
            
            clear_result = self.redis_service.clear_feed(user_id)
            current_size_after = self.redis_service.get_feed_size(user_id)
            print(f"✅ Clear operation result: {clear_result}")
            print(f"📊 Feed size after clear: {current_size_after}")
            
            # Get all available videos from S3
            print("📁 Getting available videos from S3...")
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
            
            print(f"📹 Found {len(all_videos)} videos in S3")
            print(f"🎯 Populating feed with exactly {self.target_feed_size} videos...")
            
            # Generate initial queue (repeat videos if necessary to reach target size)
            videos_added = self._populate_feed_queue(user_id, all_videos, self.target_feed_size)
            
            print(f"✅ Population completed, added {videos_added} videos")
            
            # Set feed expiry (24 hours)
            self.redis_service.set_feed_expiry(user_id, 24 * 3600)
            
            final_feed_size = self.redis_service.get_feed_size(user_id)
            generation_time = time.time() - start_time
            
            print(f"📊 FINAL FEED SIZE: {final_feed_size} (expected: {self.target_feed_size})")
            
            if final_feed_size != self.target_feed_size:
                print(f"⚠️  WARNING: Final feed size ({final_feed_size}) doesn't match target ({self.target_feed_size})")
            else:
                print(f"✅ Feed size matches target perfectly!")
            
            pass  # Initialized infinite feed for user
            
            return FeedGenerationResponse(
                success=True,
                user_id=user_id,
                videos_added=videos_added,
                total_feed_size=final_feed_size,
                generation_time=generation_time,
                message=f"Infinite feed initialized with {videos_added} videos"
            )
            
        except Exception as e:
            pass  # Failed to initialize infinite feed for user
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
        Refill the infinite feed queue when it gets low while maintaining exactly 10 videos
        
        Args:
            user_id: User to refill feed for
            
        Returns:
            True if refill was successful
        """
        try:
            print(f"🔄 REFILLING INFINITE FEED")
            print(f"👤 User: {user_id}")
            
            # Get current feed size and clear it completely for fresh preference-based rebuild
            current_size = self.redis_service.get_feed_size(user_id)
            print(f"📊 Current feed size before refill: {current_size}")
            
            # Clear the current feed completely - we'll rebuild with updated preferences
            print("🧹 Clearing current feed for preference-based rebuild...")
            self.redis_service.clear_feed(user_id)
            cleared_size = self.redis_service.get_feed_size(user_id)
            print(f"✅ Feed cleared, size now: {cleared_size}")
            
            # Get all available videos from S3 for new feed
            all_videos = self.aws_service.list_videos(max_keys=1000)
            
            if not all_videos:
                print("❌ No videos available for refill")
                return False
            
            # Rebuild feed with exactly 10 videos using updated preferences
            print(f"🎯 Rebuilding feed with exactly {self.target_feed_size} videos...")
            videos_added = self._populate_feed_queue_with_preferences(user_id, all_videos, self.target_feed_size)
            
            final_size = self.redis_service.get_feed_size(user_id)
            print(f"✅ Refill completed - added {videos_added} videos, final size: {final_size}")
            
            return videos_added > 0
            
        except Exception as e:
            pass  # Failed to refill infinite feed for user
            return False
    
    def _trigger_preference_update_if_needed(self, user_id: str) -> None:
        """
        Trigger preference update when feed is running low instead of waiting for 15 interactions
        
        Args:
            user_id: User identifier
        """
        try:
            # Import here to avoid circular imports
            from app.services.user_preference_service import UserPreferenceService
            
            user_preference_service = UserPreferenceService()
            
            # Check if user has enough interactions to justify an update (minimum threshold)
            interactions_count = user_preference_service._get_interactions_since_update(user_id)
            
            # Only update if user has at least 3 interactions since last update
            # This prevents updating on every refill if user just started
            if interactions_count >= 3:
                print(f"\n🎯 PREFERENCE UPDATE TRIGGERED")
                print(f"👤 User: {user_id}")
                print(f"🔢 Interactions since last update: {interactions_count}")
                print(f"🎮 Reason: Feed running low (< 2 videos remaining)")
                print("🧮 Calculating new preference vector from user interactions...")
                
                # Force preference update by calculating new vector and saving it
                new_preference = user_preference_service._calculate_preference_vector(user_id)
                if new_preference:
                    print(f"✅ New preference vector calculated ({len(new_preference)} dimensions)")
                    print("💾 Saving preference vector to database...")
                    
                    user_preference_service._save_user_preference(user_id, new_preference)
                    user_preference_service._reset_interaction_counter(user_id)
                    
                    # Trigger video generation for the new preference vector
                    self._trigger_video_generation_for_preference(user_id, new_preference)
                    
                    print(f"✅ PREFERENCE UPDATE COMPLETED for user {user_id}")
                    print("🎬 Video generation triggered for new preferences")
                    print("🔄 Next feed refill will use updated preferences")
                else:
                    print(f"❌ PREFERENCE UPDATE FAILED: Could not calculate preference vector for user {user_id}")
            else:
                print(f"\n📊 PREFERENCE UPDATE SKIPPED")
                print(f"👤 User: {user_id}")
                print(f"🔢 Interactions since last update: {interactions_count} (minimum: 3)")
                print("⏳ Will update when user has more interactions")
                
        except Exception as e:
            print(f"❌ Error triggering preference update for user {user_id}: {e}")
            # Don't raise - feed should continue working even if preference update fails
    
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
                pass  # Failed to add video to infinite feed for user
        
        return videos_added
    
    def _populate_feed_queue_with_preferences(self, user_id: str, available_videos: List[VideoListItem], 
                                            target_count: int) -> int:
        """
        Populate the feed queue with videos scored by user preferences
        
        Args:
            user_id: User to populate feed for
            available_videos: List of available videos from S3
            target_count: Number of videos to add (should be 10)
            
        Returns:
            Number of videos actually added
        """
        try:
            # Import here to avoid circular imports
            from app.services.user_preference_service import UserPreferenceService
            from app.services.pinecone_service import PineconeService
            
            print(f"🎯 Populating feed with preference-based scoring...")
            print(f"📚 Available videos: {len(available_videos)}")
            print(f"🎯 Target videos: {target_count}")
            
            # Get user's current preference vector
            user_preference_service = UserPreferenceService()
            pinecone_service = PineconeService()
            
            user_preference = user_preference_service.get_user_preference(user_id)
            
            if not user_preference or not user_preference.preference_embedding:
                print("⚠️  No user preference found, falling back to random scoring")
                return self._populate_feed_queue(user_id, available_videos, target_count, append=False)
            
            preference_vector = user_preference.preference_embedding
            print(f"✅ Using preference vector with {len(preference_vector)} dimensions")
            
            # Score all videos based on preference similarity
            scored_videos = []
            
            for video in available_videos:
                try:
                    # Get video embedding from Pinecone
                    video_embedding = pinecone_service.get_video_embedding(video.video_id)
                    
                    if video_embedding:
                        # Calculate cosine similarity between user preference and video embedding
                        similarity = self._cosine_similarity(preference_vector, video_embedding)
                        scored_videos.append((video.video_id, similarity))
                        print(f"📹 Video {video.video_id[:8]}... similarity: {similarity:.3f}")
                    else:
                        # Fallback: random score for videos without embeddings
                        fallback_score = random.random() * 0.3  # Lower than preference-based scores
                        scored_videos.append((video.video_id, fallback_score))
                        print(f"📹 Video {video.video_id[:8]}... fallback score: {fallback_score:.3f}")
                        
                except Exception as e:
                    print(f"⚠️  Error scoring video {video.video_id}: {e}")
                    continue
            
            if not scored_videos:
                print("❌ No videos could be scored, falling back to random")
                return self._populate_feed_queue(user_id, available_videos, target_count, append=False)
            
            # Sort by similarity score (highest first)
            scored_videos.sort(key=lambda x: x[1], reverse=True)
            
            # Take top videos up to target count
            videos_to_add = scored_videos[:target_count]
            
            print(f"🎯 Selected top {len(videos_to_add)} videos by preference similarity:")
            for i, (video_id, score) in enumerate(videos_to_add, 1):
                print(f"   {i}. {video_id[:8]}... score: {score:.3f}")
            
            # Add videos to Redis feed with their similarity scores
            videos_added = 0
            for video_id, score in videos_to_add:
                if self.redis_service.add_to_feed(user_id, video_id, score):
                    videos_added += 1
                else:
                    print(f"❌ Failed to add video {video_id} to feed")
            
            print(f"✅ Added {videos_added} preference-scored videos to feed")
            return videos_added
            
        except Exception as e:
            print(f"❌ Error in preference-based feed population: {e}")
            # Fallback to random scoring
            return self._populate_feed_queue(user_id, available_videos, target_count, append=False)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            import math
            
            # Ensure both vectors are the same length
            if len(vec1) != len(vec2):
                print(f"⚠️  Vector length mismatch: {len(vec1)} vs {len(vec2)}")
                return 0.0
            
            # Calculate dot product and magnitudes
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            similarity = dot_product / (magnitude1 * magnitude2)
            return max(0.0, similarity)  # Ensure non-negative
            
        except Exception as e:
            print(f"❌ Error calculating cosine similarity: {e}")
            return 0.0
    
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
                    pass  # Video not found in S3, skipping
                    
            except Exception as e:
                pass  # Failed to hydrate video
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
            pass  # Failed to get infinite feed stats for user
            return FeedStatsResponse(
                user_id=user_id,
                feed_size=0,
                videos_consumed=0,
                last_refresh=None,
                is_healthy=False
            )
    
    def _trigger_video_generation_for_preference(self, user_id: str, preference_vector: List[float]) -> None:
        """
        Trigger video generation when preference vector is updated
        
        Args:
            user_id: User identifier
            preference_vector: Updated preference vector
        """
        try:
            # Import here to avoid circular imports
            from app.services.video_generation_queue_service import VideoGenerationQueueService
            
            print(f"🎬 Triggering video generation for updated preferences")
            queue_service = VideoGenerationQueueService()
            result = queue_service.process_new_preference_vector(user_id, preference_vector)
            
            if result.get("success"):
                print(f"✅ Video generation triggered successfully")
            else:
                print(f"⚠️  Video generation trigger failed: {result.get('message', 'unknown error')}")
                
        except Exception as e:
            print(f"❌ Error triggering video generation: {e}")
            # Don't raise - preference update should succeed even if video generation fails 