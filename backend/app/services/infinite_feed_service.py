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
            
            # Track shown videos for diversity improvement
            if feed_videos:
                shown_video_ids = [video.video_id for video in feed_videos]
                self._track_shown_videos(request.user_id, shown_video_ids)
            
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
            # Shuffle the available videos for this round to ensure variety
            shuffled_videos = available_videos.copy()
            random.shuffle(shuffled_videos)
            
            for video in shuffled_videos:
                if len(videos_to_add) >= target_count:
                    break
                
                # Make video ID unique by adding round number and position
                # This allows the same video to appear multiple times in the queue
                unique_video_id = f"{video.video_id}:{round_number}:{len(videos_to_add)}"
                
                # Generate a more varied random score with better distribution
                # Use different random distributions for better variety
                base_score = random.uniform(0.1, 0.9)  # Base score between 0.1 and 0.9
                time_factor = (time.time() % 100) / 1000  # Small time-based variation
                round_bonus = round_number * 0.01  # Small bonus for later rounds
                position_noise = random.gauss(0, 0.05)  # Gaussian noise
                
                score = max(0.0, base_score + time_factor + round_bonus + position_noise)
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
            
            # Get recently shown videos to add diversity by avoiding immediate repeats
            recently_shown = self._get_recently_shown_videos(user_id)
            print(f"📚 Recently shown videos: {len(recently_shown)}")
            
            # Score all videos based on preference similarity
            scored_videos = []
            
            for video in available_videos:
                try:
                    # Get video embedding from Pinecone
                    video_embedding = pinecone_service.get_video_embedding(video.video_id)
                    
                    if video_embedding:
                        # Calculate cosine similarity between user preference and video embedding
                        similarity = self._cosine_similarity(preference_vector, video_embedding)
                        
                        # Apply diversity penalty for recently shown videos
                        if video.video_id in recently_shown:
                            diversity_penalty = 0.3  # Reduce score by 30% for recently shown videos
                            similarity = similarity * (1 - diversity_penalty)
                            print(f"📹 Video {video.video_id[:8]}... similarity: {similarity:.3f} (recently shown, penalty applied)")
                        else:
                            print(f"📹 Video {video.video_id[:8]}... similarity: {similarity:.3f}")
                        
                        scored_videos.append((video.video_id, similarity))
                    else:
                        # Fallback: random score for videos without embeddings
                        fallback_score = random.random() * 0.3  # Lower than preference-based scores
                        
                        # Apply diversity penalty for recently shown videos
                        if video.video_id in recently_shown:
                            fallback_score = fallback_score * 0.5  # Reduce score by 50% for recently shown videos
                            print(f"📹 Video {video.video_id[:8]}... fallback score: {fallback_score:.3f} (recently shown, penalty applied)")
                        else:
                            print(f"📹 Video {video.video_id[:8]}... fallback score: {fallback_score:.3f}")
                        
                        scored_videos.append((video.video_id, fallback_score))
                        
                except Exception as e:
                    print(f"⚠️  Error scoring video {video.video_id}: {e}")
                    continue
            
            if not scored_videos:
                print("❌ No videos could be scored, falling back to random")
                return self._populate_feed_queue(user_id, available_videos, target_count, append=False)
            
            # Add variety and randomization to video selection for better diversity
            # Instead of always taking the exact same top videos, use weighted random selection
            
            # Step 1: Add small random noise to scores to create variation while preserving preferences
            for i in range(len(scored_videos)):
                video_id, original_score = scored_videos[i]
                # Add random noise (±5% of score) to introduce variety while keeping relative preferences
                noise = random.uniform(-0.05, 0.05) * original_score if original_score > 0 else random.uniform(-0.02, 0.02)
                noisy_score = max(0.0, original_score + noise)
                scored_videos[i] = (video_id, noisy_score)
            
            # Step 2: Sort by noisy similarity score (highest first)
            scored_videos.sort(key=lambda x: x[1], reverse=True)
            
            # Step 3: Use weighted random selection for diversity
            # Take top 60% of videos for guaranteed quality, then weighted random for the rest
            guaranteed_count = max(1, int(target_count * 0.6))  # At least 60% from top videos
            exploration_count = target_count - guaranteed_count
            
            videos_to_add = []
            
            # Add guaranteed high-quality videos (top 60%)
            top_videos = scored_videos[:min(guaranteed_count * 2, len(scored_videos))]  # Pool of top videos to choose from
            random.shuffle(top_videos)  # Randomize even the top videos
            videos_to_add.extend(top_videos[:guaranteed_count])
            
            # Add exploration videos using weighted random selection
            if exploration_count > 0 and len(scored_videos) > guaranteed_count:
                remaining_videos = [v for v in scored_videos if v not in videos_to_add]
                
                if remaining_videos:
                    # Use weighted random selection based on scores
                    exploration_videos = self._weighted_random_selection(
                        remaining_videos, 
                        min(exploration_count, len(remaining_videos))
                    )
                    videos_to_add.extend(exploration_videos)
            
            # Ensure we have exactly target_count videos
            while len(videos_to_add) < target_count and len(videos_to_add) < len(scored_videos):
                remaining = [v for v in scored_videos if v not in videos_to_add]
                if remaining:
                    videos_to_add.append(random.choice(remaining))
                else:
                    break
            
            # Final shuffle to randomize order
            random.shuffle(videos_to_add)
            videos_to_add = videos_to_add[:target_count]
            
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
    
    def _weighted_random_selection(self, scored_videos: List[tuple], count: int) -> List[tuple]:
        """
        Perform weighted random selection of videos based on their scores
        
        Args:
            scored_videos: List of (video_id, score) tuples
            count: Number of videos to select
            
        Returns:
            List of selected (video_id, score) tuples
        """
        if not scored_videos or count <= 0:
            return []
        
        if count >= len(scored_videos):
            return scored_videos.copy()
        
        try:
            # Extract scores and ensure they're positive for weighted selection
            scores = [max(0.001, score) for _, score in scored_videos]  # Minimum weight of 0.001
            
            # Normalize scores to create probability weights
            total_score = sum(scores)
            if total_score <= 0:
                # Fallback to uniform random selection if all scores are zero
                return random.sample(scored_videos, count)
            
            weights = [score / total_score for score in scores]
            
            # Perform weighted random selection without replacement
            selected = []
            remaining_videos = scored_videos.copy()
            remaining_weights = weights.copy()
            
            for _ in range(count):
                if not remaining_videos:
                    break
                
                # Weighted random choice
                selected_idx = random.choices(range(len(remaining_videos)), weights=remaining_weights, k=1)[0]
                selected.append(remaining_videos[selected_idx])
                
                # Remove selected video and its weight
                remaining_videos.pop(selected_idx)
                remaining_weights.pop(selected_idx)
                
                # Renormalize weights
                if remaining_weights:
                    total_weight = sum(remaining_weights)
                    if total_weight > 0:
                        remaining_weights = [w / total_weight for w in remaining_weights]
            
            return selected
            
        except Exception as e:
            print(f"❌ Error in weighted random selection: {e}")
            # Fallback to simple random selection
            return random.sample(scored_videos, min(count, len(scored_videos)))
    
    def _get_recently_shown_videos(self, user_id: str) -> set:
        """
        Get set of recently shown video IDs to avoid immediate repeats
        
        Args:
            user_id: User identifier
            
        Returns:
            Set of recently shown video IDs
        """
        try:
            # Get the last 20 videos shown to user from Redis
            recent_key = f"recent_videos:{user_id}"
            recent_videos = self.redis_service.get_client().lrange(recent_key, 0, 19)  # Last 20 videos
            return set(video_id.decode('utf-8') if isinstance(video_id, bytes) else video_id for video_id in recent_videos)
        except Exception as e:
            print(f"❌ Error getting recently shown videos: {e}")
            return set()
    
    def _track_shown_videos(self, user_id: str, video_ids: List[str]) -> None:
        """
        Track videos that have been shown to user to improve diversity
        
        Args:
            user_id: User identifier
            video_ids: List of video IDs that were shown
        """
        try:
            recent_key = f"recent_videos:{user_id}"
            client = self.redis_service.get_client()
            
            # Add each video to the front of the list
            for video_id in video_ids:
                # Extract original video ID if it's a unique ID
                original_id = video_id.split(':')[0] if ':' in video_id else video_id
                client.lpush(recent_key, original_id)
            
            # Keep only the last 50 videos (trim the list)
            client.ltrim(recent_key, 0, 49)
            
            # Set expiry for 7 days
            client.expire(recent_key, 7 * 24 * 3600)
            
        except Exception as e:
            print(f"❌ Error tracking shown videos: {e}")
    
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