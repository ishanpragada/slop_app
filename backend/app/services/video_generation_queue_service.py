import os
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from app.services.redis_service import RedisService
from app.services.pinecone_service import PineconeService
from app.services.database_service import DatabaseService
from app.services.prompt_generation_service import PromptGenerationService

class VideoGenerationQueueService:
    """Service for managing video generation queues based on user preferences"""
    
    def __init__(self):
        load_dotenv()
        
        # Configuration
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", 0.1))  # Reasonable cosine similarity threshold
        self.min_similar_prompts = 3  # Minimum number of similar prompts required
        
        # Initialize services
        self.redis_service = RedisService()
        self.pinecone_service = PineconeService()
        self.database_service = DatabaseService()
        self.prompt_service = PromptGenerationService()
    
    def process_new_preference_vector(self, user_id: str, preference_vector: List[float]) -> Dict[str, Any]:
        """
        Process a new user preference vector and create video generation queue
        
        Args:
            user_id: User identifier
            preference_vector: New user preference vector (1536 dimensions)
            
        Returns:
            Dictionary with processing results
        """
        try:
            pass  # Processing new preference vector
            
            # Step 1: Find similar prompt embeddings
            similar_prompts, above_threshold_count = self._find_similar_prompt_embeddings(preference_vector)
            
            # TEMPORARY: Force processing existing videos only, no generation
            pass  # TEMPORARY MODE: Video generation disabled
            pass  # Found similar prompts, using existing videos
            
            # Force to process existing videos regardless of threshold
            return self._process_existing_similar_prompts_force_three(user_id, similar_prompts)
                
        except Exception as e:
            pass  # Error processing preference vector
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process preference vector"
            }
    
    def _find_similar_prompt_embeddings(self, preference_vector: List[float]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find prompt embeddings similar to the user preference vector
        
        Args:
            preference_vector: User preference vector
            
        Returns:
            Tuple of (similar prompts list, count of prompts above threshold)
        """
        try:
            # We need to convert user preference vector to a prompt-like query
            # For now, we'll search for prompts using a generic query and then filter by similarity
            
            # Get all available prompts from Pinecone (we'll implement better search later)
            index = self.pinecone_service.pc.Index(self.pinecone_service.index_name)
            
            # Query with a broad search to get candidates using Pinecone v7 API
            results = index.search(
                namespace="ns1",
                query={
                    "inputs": {"text": "cinematic video content"},  # Generic query to get candidates
                    "top_k": 100  # Get more candidates to ensure we have at least 3
                },
                fields=["prompt"]
                # Note: include_values is not supported in this version
            )
            
            similar_prompts = []
            
            # Collect all results and apply threshold
            above_threshold = []
            all_results = []
            
            for hit in results.result.hits:
                # Use Pinecone's similarity score as a proxy for our similarity
                pinecone_score = hit._score if hasattr(hit, '_score') else 0.0
                
                prompt_data = {
                    "prompt": hit.fields.get("prompt", ""),
                    "video_id": hit._id,
                    "similarity_score": pinecone_score,
                    "embedding": None,  # We'll get this separately if needed
                    "metadata": {
                        "video_id": hit._id,
                        "pinecone_score": pinecone_score,
                        "preference_similarity": pinecone_score
                    }
                }
                
                # Add to all results
                all_results.append(prompt_data)
                
                # Check if above threshold
                if pinecone_score >= (self.similarity_threshold * 0.5):  # Adjust threshold for Pinecone scores
                    above_threshold.append(prompt_data)
            
            # Sort both lists by similarity score
            above_threshold.sort(key=lambda x: x["similarity_score"], reverse=True)
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            above_threshold_count = len(above_threshold)
            
            # TEMPORARY: Always return all results for forced selection method
            pass  # Found prompts, returning all results for forced selection
            
            # Return all results (sorted by similarity) for forced selection
            similar_prompts = all_results
            
            return similar_prompts, above_threshold_count
            
        except Exception as e:
            pass  # Error finding similar prompt embeddings
            return [], 0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Handle different vector formats
            if hasattr(vec2, 'values'):
                vec2 = vec2.values
            elif hasattr(vec2, '__iter__') and not isinstance(vec2, list):
                vec2 = list(vec2)
            
            # Ensure both vectors are lists and same length
            if len(vec1) != len(vec2):
                print(f"⚠️  Vector length mismatch: {len(vec1)} vs {len(vec2)}")
                return 0.0
            
            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception as e:
            pass  # Error calculating cosine similarity
            return 0.0
    
    def _process_existing_similar_prompts(self, user_id: str, similar_prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process existing similar prompts by adding their videos to the queue
        
        Args:
            user_id: User identifier
            similar_prompts: List of similar prompts with video IDs
            
        Returns:
            Processing results
        """
        try:
            # Take all available similar prompts (should be 3+ if above threshold)
            selected_prompts = similar_prompts
            
            # Get video IDs and retrieve from database
            video_ids = []
            valid_videos = []
            
            for prompt_data in selected_prompts:
                video_id = prompt_data["video_id"]
                
                # Verify video exists in PostgreSQL
                video_info = self.database_service.get_video_by_id(video_id)
                if video_info:
                    video_ids.append(video_id)
                    valid_videos.append({
                        "video_id": video_id,
                        "prompt": prompt_data["prompt"],
                        "similarity_score": prompt_data["similarity_score"],
                        "s3_url": video_info.get("s3_url"),
                        "created_at": video_info.get("created_at")
                    })
                    pass  # Verified video exists in database
                else:
                    print(f"⚠️  Video {video_id} not found in database")
            
            if not valid_videos:
                pass  # No valid videos found for similar prompts
                return {
                    "success": False,
                    "message": "No valid videos found for similar prompts"
                }
            
            # Add videos to Redis queue
            queue_result = self._add_videos_to_queue(user_id, valid_videos)
            
            # Add videos to User Feed Queue for immediate consumption
            self._add_videos_to_user_feed(user_id, valid_videos)
            
            return {
                "success": True,
                "strategy": "existing_videos",
                "videos_found": len(valid_videos),
                "videos_queued": queue_result.get("videos_added", 0),
                "similarity_threshold": self.similarity_threshold,
                "queue_result": queue_result,
                "videos": valid_videos
            }
            
        except Exception as e:
            pass  # Error processing existing similar prompts
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process existing similar prompts"
            }
    
    def _process_existing_similar_prompts_force_three(self, user_id: str, similar_prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        TEMPORARY: Process existing similar prompts by forcing to use exactly 3 closest videos
        This method ignores similarity thresholds and always picks the 3 closest videos available
        
        Args:
            user_id: User identifier
            similar_prompts: List of similar prompts with video IDs (sorted by similarity)
            
        Returns:
            Processing results
        """
        try:
            # Take the top 3 closest videos regardless of distance/similarity
            selected_prompts = similar_prompts[:3] if len(similar_prompts) >= 3 else similar_prompts
            
            print(f"🎯 FORCED SELECTION: Using top {len(selected_prompts)} closest existing videos")
            
            # Get video IDs and retrieve from database
            valid_videos = []
            
            for i, prompt_data in enumerate(selected_prompts):
                video_id = prompt_data["video_id"]
                prompt_text = prompt_data["prompt"]
                similarity_score = prompt_data["similarity_score"]
                
                # Verify video exists in PostgreSQL
                video_info = self.database_service.get_video_by_id(video_id)
                if video_info:
                    valid_videos.append({
                        "video_id": video_id,
                        "prompt": prompt_text,
                        "similarity_score": similarity_score,
                        "s3_url": video_info.get("s3_url"),
                        "created_at": video_info.get("created_at")
                    })
                    pass  # Selected video for queue
                else:
                    print(f"⚠️  Video {video_id} not found in database, skipping")
            
            if not valid_videos:
                pass  # No valid videos found in database
                return {
                    "success": False,
                    "message": "No valid videos found in database"
                }
            
            pass  # Final selection of videos for queue
            
            # TEMPORARY: Clear some space at the top of the feed for immediate visibility
            self._clear_feed_space_for_new_videos(user_id, len(valid_videos))
            
            # Log all prompts being added to queue
            pass  # Adding prompts to queue
            for i, video in enumerate(valid_videos, 1):
                print(f"   {i}. Video ID: {video['video_id']}")
                print(f"      Prompt: '{video['prompt']}'")
                print(f"      Similarity Score: {video['similarity_score']:.3f}")
                print(f"      S3 URL: {video.get('s3_url', 'N/A')}")
                print()
            
            # Add videos to Redis queue
            queue_result = self._add_videos_to_queue(user_id, valid_videos)
            
            # Add videos to User Feed Queue for immediate consumption
            self._add_videos_to_user_feed(user_id, valid_videos)
            
            return {
                "success": True,
                "strategy": "forced_existing_videos",
                "videos_found": len(valid_videos),
                "videos_queued": queue_result.get("videos_added", 0),
                "threshold_bypassed": True,
                "queue_result": queue_result,
                "videos": valid_videos
            }
            
        except Exception as e:
            pass  # Error processing forced existing similar prompts
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process forced existing similar prompts"
            }
    
    def _generate_new_similar_prompts(self, user_id: str, existing_prompts: List[Dict[str, Any]], preference_vector: List[float]) -> Dict[str, Any]:
        """
        Generate new similar prompts using LLM when not enough existing ones are found
        
        Args:
            user_id: User identifier
            existing_prompts: List of existing similar prompts (may be empty)
            preference_vector: User preference vector
            
        Returns:
            Generation results
        """
        try:
            print("🤖 Generating new similar prompts using LLM...")
            
            # Extract existing prompt for context
            existing_prompt_texts = [p["prompt"] for p in existing_prompts[:1]]
            
            # Generate new prompts based on existing ones or preference
            new_prompts = self._generate_prompts_with_llm(existing_prompt_texts)
            
            if not new_prompts:
                pass  # Failed to generate new prompts
                return {
                    "success": False,
                    "message": "Failed to generate new prompts with LLM"
                }
            
            # Add new prompts to generation queue
            queue_result = self._add_prompts_to_generation_queue(user_id, new_prompts, preference_vector)
            
            return {
                "success": True,
                "strategy": "generated_prompts",
                "existing_prompts_count": len(existing_prompts),
                "new_prompts_generated": len(new_prompts),
                "prompts_queued": queue_result.get("prompts_added", 0),
                "queue_result": queue_result,
                "generated_prompts": new_prompts
            }
            
        except Exception as e:
            pass  # Error generating new similar prompts
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate new similar prompts"
            }
    
    def _generate_prompts_with_llm(self, reference_prompts: List[str]) -> List[str]:
        """
        Use LLM to generate similar prompts based on reference prompts
        
        Args:
            reference_prompts: List of reference prompts for similarity
            
        Returns:
            List of generated prompts
        """
        try:
            if reference_prompts:
                # Create a prompt for the LLM based on existing prompts
                reference_text = "\n".join([f"- {prompt}" for prompt in reference_prompts])
                llm_prompt = f"""
                Based on these video prompts:
                {reference_text}
                
                Generate 1 new video prompt that is similar in theme and mood but with different specific content.
                The prompt should be suitable for an 8-second video and be visually interesting, funny, engaging, etc.
                
                Requirements:
                - Similar visual style or theme to the reference prompts
                - Different specific actions or scenarios
                - Suitable for 8-second videos
                - Engaging and visually compelling
                
                Return only the prompt, without numbering or bullets.
                """
            else:
                # Fallback: generate general creative prompts
                llm_prompt = """
                Generate 1 creative and engaging video prompt suitable for 8-second videos.
                It should be visually interesting and suitable for social media content.
                
                Focus on:
                - Relatable everyday situations with a twist
                - Visually compelling scenarios
                - Clear subjects and actions
                - Engaging content that works in 8 seconds
                
                Return only the prompt, without numbering or bullets.
                """
            
            # Use the existing prompt generation service
            response = self.prompt_service.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=llm_prompt
            )
            
            if response and response.text:
                # Parse the response to extract individual prompts
                raw_prompts = response.text.strip().split('\n')
                new_prompts = []
                
                for prompt in raw_prompts:
                    cleaned_prompt = prompt.strip()
                    # Remove any numbering or bullets
                    if cleaned_prompt and not cleaned_prompt.startswith(('1.', '2.', '3.', '-', '*')):
                        new_prompts.append(cleaned_prompt)
                    elif cleaned_prompt:
                        # Remove numbering/bullets and add
                        cleaned_prompt = cleaned_prompt.split('.', 1)[-1].strip() if '.' in cleaned_prompt else cleaned_prompt.lstrip('-* ')
                        if cleaned_prompt:
                            new_prompts.append(cleaned_prompt)
                
                # Ensure we have exactly 1 prompt
                new_prompts = new_prompts[:1]
                
                pass  # Generated new prompts using LLM
                for i, prompt in enumerate(new_prompts, 1):
                    print(f"   {i}. {prompt}")
                
                return new_prompts
            else:
                pass  # LLM returned empty response
                return []
                
        except Exception as e:
            pass  # Error generating prompts with LLM
            return []
    
    def _add_videos_to_queue(self, user_id: str, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add existing videos to the user's video generation queue in Redis
        
        Args:
            user_id: User identifier
            videos: List of video information
            
        Returns:
            Queue operation results
        """
        try:
            queue_key = f"video_queue:{user_id}"
            videos_added = 0
            
            for video in videos:
                queue_item = {
                    "type": "existing_video",
                    "video_id": video["video_id"],
                    "prompt": video["prompt"],
                    "s3_url": video.get("s3_url"),
                    "similarity_score": video.get("similarity_score", 0.0),
                    "added_at": datetime.now().isoformat(),
                    "status": "ready"
                }
                
                # Add to Redis queue with a score (higher similarity = higher priority)
                score = video.get("similarity_score", 0.0)
                success = self.redis_service.get_client().zadd(
                    queue_key, 
                    {json.dumps(queue_item): score}
                )
                
                if success:
                    videos_added += 1
                    pass  # Added video to queue
                    print(f"   📝 Prompt: '{video['prompt']}'")
                    print(f"   🔗 S3 URL: {video.get('s3_url', 'N/A')}")
            
            # Set expiry for the queue (24 hours)
            self.redis_service.get_client().expire(queue_key, 24 * 3600)
            
            return {
                "success": True,
                "videos_added": videos_added,
                "queue_key": queue_key,
                "total_in_queue": self.redis_service.get_client().zcard(queue_key)
            }
            
        except Exception as e:
            pass  # Error adding videos to queue
            return {
                "success": False,
                "error": str(e),
                "videos_added": 0
            }
    
    def _add_prompts_to_generation_queue(self, user_id: str, prompts: List[str], preference_vector: List[float]) -> Dict[str, Any]:
        """
        Add new prompts to the video generation queue in Redis
        
        Args:
            user_id: User identifier
            prompts: List of prompts to generate videos for
            preference_vector: User preference vector for context
            
        Returns:
            Queue operation results
        """
        try:
            queue_key = f"video_queue:{user_id}"
            prompts_added = 0
            
            for i, prompt in enumerate(prompts):
                queue_item = {
                    "type": "generate_video",
                    "prompt": prompt,
                    "preference_vector": preference_vector,
                    "user_id": user_id,
                    "added_at": datetime.now().isoformat(),
                    "status": "pending_generation",
                    "priority": len(prompts) - i  # Earlier prompts get higher priority
                }
                
                # Add to Redis queue with priority score
                score = len(prompts) - i  # Higher number = higher priority
                success = self.redis_service.get_client().zadd(
                    queue_key,
                    {json.dumps(queue_item): score}
                )
                
                if success:
                    prompts_added += 1
                    pass  # Added prompt to generation queue
            
            # Set expiry for the queue (24 hours)
            self.redis_service.get_client().expire(queue_key, 24 * 3600)
            
            return {
                "success": True,
                "prompts_added": prompts_added,
                "queue_key": queue_key,
                "total_in_queue": self.redis_service.get_client().zcard(queue_key)
            }
            
        except Exception as e:
            pass  # Error adding prompts to generation queue
            return {
                "success": False,
                "error": str(e),
                "prompts_added": 0
            }
    
    def get_user_queue_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current status of a user's video generation queue
        
        Args:
            user_id: User identifier
            
        Returns:
            Queue status information
        """
        try:
            queue_key = f"video_queue:{user_id}"
            client = self.redis_service.get_client()
            
            # Get queue size
            queue_size = client.zcard(queue_key)
            
            if queue_size == 0:
                return {
                    "success": True,
                    "queue_size": 0,
                    "message": "No items in queue"
                }
            
            # Get all items in queue (with scores)
            queue_items_raw = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            queue_items = []
            for item_json, score in queue_items_raw:
                try:
                    item = json.loads(item_json)
                    item["queue_score"] = score
                    queue_items.append(item)
                except json.JSONDecodeError:
                    continue
            
            # Categorize items
            existing_videos = [item for item in queue_items if item.get("type") == "existing_video"]
            pending_generation = [item for item in queue_items if item.get("type") == "generate_video"]
            
            return {
                "success": True,
                "queue_size": queue_size,
                "existing_videos": len(existing_videos),
                "pending_generation": len(pending_generation),
                "items": queue_items
            }
            
        except Exception as e:
            pass  # Error getting queue status
            return {
                "success": False,
                "error": str(e),
                "queue_size": 0
            }
    
    def get_next_generation_task(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next video generation task from the user's queue
        
        Args:
            user_id: User identifier
            
        Returns:
            Next generation task or None if queue is empty
        """
        try:
            queue_key = f"video_queue:{user_id}"
            client = self.redis_service.get_client()
            
            # Get the highest priority item that needs generation
            queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            for item_json, score in queue_items:
                try:
                    item = json.loads(item_json)
                    
                    # Look for items that need generation
                    if item.get("type") == "generate_video" and item.get("status") == "pending_generation":
                        # Mark as in progress and return
                        item["status"] = "in_progress"
                        item["started_at"] = datetime.now().isoformat()
                        
                        # Update in queue
                        client.zrem(queue_key, item_json)
                        client.zadd(queue_key, {json.dumps(item): score})
                        
                        return item
                        
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            pass  # Error getting next generation task
            return None
    
    def mark_generation_complete(self, user_id: str, task: Dict[str, Any], video_id: str, s3_url: str) -> bool:
        """
        Mark a generation task as complete and update with video info
        
        Args:
            user_id: User identifier
            task: The generation task that was completed
            video_id: Generated video ID
            s3_url: S3 URL of generated video
            
        Returns:
            Success status
        """
        try:
            queue_key = f"video_queue:{user_id}"
            client = self.redis_service.get_client()
            
            # Update task status
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["video_id"] = video_id
            task["s3_url"] = s3_url
            task["type"] = "existing_video"  # Now it's an available video
            
            # Find and replace the task in queue
            queue_items = client.zrevrange(queue_key, 0, -1, withscores=True)
            
            for item_json, score in queue_items:
                try:
                    item = json.loads(item_json)
                    
                    # Match by prompt and user_id
                    if (item.get("prompt") == task.get("prompt") and 
                        item.get("user_id") == task.get("user_id")):
                        
                        # Remove old task and add updated one
                        client.zrem(queue_key, item_json)
                        client.zadd(queue_key, {json.dumps(task): score})
                        
                        pass  # Marked generation task as complete
                        return True
                        
                except json.JSONDecodeError:
                    continue
            
            return False
            
        except Exception as e:
            pass  # Error marking generation complete
            return False
    
    def _add_videos_to_user_feed(self, user_id: str, videos: List[Dict[str, Any]]) -> None:
        """
        Add videos to the user's feed queue for immediate consumption
        
        Args:
            user_id: User identifier
            videos: List of video information with video_id, similarity_score, etc.
        """
        try:
            videos_added = 0
            
            for video in videos:
                video_id = video.get("video_id")
                similarity_score = video.get("similarity_score", 0.0)
                
                if video_id:
                    # TEMPORARY: Use high timestamp-based scores to ensure these videos appear FIRST
                    # This will place them at the front of the feed for immediate visibility
                    import time
                    base_timestamp = time.time() * 1000  # Current timestamp in milliseconds
                    feed_score = base_timestamp + (similarity_score * 100)  # Add similarity as bonus
                    
                    pass  # High priority feed score calculated
                    
                    success = self.redis_service.add_to_feed(user_id, video_id, feed_score)
                    if success:
                        videos_added += 1
                        pass  # Added video to user feed
                    else:
                        pass  # Failed to add video to user feed
            
            pass  # Added videos to User Feed Queue
            
        except Exception as e:
            pass  # Error adding videos to user feed
    
    def _clear_feed_space_for_new_videos(self, user_id: str, num_new_videos: int) -> None:
        """
        TEMPORARY: Clear some space at the top of the feed to ensure new videos are immediately visible
        
        Args:
            user_id: User identifier
            num_new_videos: Number of new videos that will be added
        """
        try:
            client = self.redis_service.get_client()
            feed_key = f"user:feed:{user_id}"
            
            # Get current feed size
            current_size = client.zcard(feed_key)
            pass  # Current feed size noted
            
            if current_size > 50:  # Only clear if feed is getting long
                # Remove some older/lower-scored videos to make room
                # Remove the bottom 25% of videos to keep feed manageable
                videos_to_remove = max(10, current_size // 4)
                
                pass  # Removing older videos to make room
                removed = client.zremrangebyrank(feed_key, 0, videos_to_remove - 1)
                pass  # Removed older videos from feed
                
                # Update feed size
                new_size = client.zcard(feed_key)
                pass  # Feed size after cleanup
            else:
                pass  # Feed size is manageable, no cleanup needed
                
        except Exception as e:
            pass  # Error clearing feed space
            # Don't raise - this is just optimization, not critical
