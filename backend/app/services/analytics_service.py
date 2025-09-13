import os
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

class AnalyticsService:
    def __init__(self):
        load_dotenv()
        
        # Database connection parameters
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'postgres'),  # Changed to match your .env
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def _get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            raise
    
    def track_interaction(
        self, 
        user_id: str, 
        video_id: str, 
        action: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a user interaction with a video
        
        Args:
            user_id: Unique user identifier
            video_id: Video identifier
            action: Type of interaction (like, comment, share, save, view)
            metadata: Additional interaction data
            
        Returns:
            Dictionary with interaction details
        """
        try:
            timestamp = datetime.now()
            
            if action == "view":
                # Update watch count and total watch time in analytics table
                self._update_video_watch_analytics(video_id, metadata.get('watch_time', 0))
            elif action == "like":
                # Update like count in videos table
                self._update_video_like_count(video_id, 1)
            elif action == "share":
                # Update share count in both videos and analytics tables
                self._update_video_share_count(video_id, 1)
            
            print(f"✅ Tracked {action} interaction for user {user_id} on video {video_id}")
            
            return {
                "success": True,
                "timestamp": timestamp.isoformat(),
                "message": f"Successfully tracked {action} interaction"
            }
            
        except Exception as e:
            print(f"❌ Error tracking interaction: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track interaction"
            }
    
    def add_comment(
        self, 
        user_id: str, 
        video_id: str, 
        comment_text: str
    ) -> Dict[str, Any]:
        """
        Add a comment to a video
        
        Args:
            user_id: Unique user identifier
            video_id: Video identifier
            comment_text: Comment content
            
        Returns:
            Dictionary with comment details
        """
        try:
            timestamp = datetime.now()
            
            # For now, we'll just track as a comment interaction
            # In a full implementation, you'd have a separate comments table
            self.track_interaction(user_id, video_id, "comment", {
                "comment_text": comment_text
            })
            
            print(f"✅ Added comment from user {user_id} on video {video_id}")
            
            return {
                "success": True,
                "timestamp": timestamp.isoformat(),
                "message": "Comment added successfully"
            }
            
        except Exception as e:
            print(f"❌ Error adding comment: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add comment"
            }
    
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific video
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with video analytics
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get video data
                    cur.execute("""
                        SELECT video_id, s3_url, prompt, length_seconds, caption, 
                               created_at, like_count, share_count
                        FROM videos 
                        WHERE video_id = %s
                    """, (video_id,))
                    video_data = cur.fetchone()
                    
                    if not video_data:
                        return {"error": "Video not found"}
                    
                    # Get analytics data
                    cur.execute("""
                        SELECT video_id, watch_count, total_watch_time, liked, share_count
                        FROM analytics 
                        WHERE video_id = %s
                    """, (video_id,))
                    analytics_data = cur.fetchone()
                    
                    # Combine data
                    result = dict(video_data)
                    if analytics_data:
                        result.update(dict(analytics_data))
                        
                        # Calculate engagement rate
                        total_interactions = (
                            result.get('like_count', 0) + 
                            result.get('share_count', 0) + 
                            result.get('watch_count', 0)
                        )
                        
                        if result.get('watch_count', 0) > 0:
                            result['engagement_rate'] = (total_interactions / result['watch_count']) * 100
                        else:
                            result['engagement_rate'] = 0
                    else:
                        # Initialize analytics if none exist
                        result.update({
                            'watch_count': 0,
                            'total_watch_time': 0,
                            'liked': False,
                            'share_count': 0,
                            'engagement_rate': 0
                        })
                    
                    return result
                    
        except Exception as e:
            print(f"❌ Error getting video analytics: {e}")
            return {"error": str(e)}
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with user analytics
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get user's interaction summary from videos and analytics tables
                    cur.execute("""
                        SELECT 
                            COUNT(DISTINCT v.video_id) as total_videos_interacted,
                            SUM(CASE WHEN a.liked THEN 1 ELSE 0 END) as videos_liked,
                            SUM(a.share_count) as total_shares,
                            SUM(a.watch_count) as total_views,
                            SUM(a.total_watch_time) as total_watch_time
                        FROM videos v
                        LEFT JOIN analytics a ON v.video_id = a.video_id
                        WHERE v.video_id IN (
                            SELECT DISTINCT video_id FROM analytics WHERE user_id = %s
                        )
                    """, (user_id,))
                    
                    result = cur.fetchone()
                    
                    if result:
                        return {
                            "user_id": user_id,
                            "total_videos_interacted": result['total_videos_interacted'] or 0,
                            "videos_liked": result['videos_liked'] or 0,
                            "total_shares": result['total_shares'] or 0,
                            "total_views": result['total_views'] or 0,
                            "total_watch_time": result['total_watch_time'] or 0,
                            "average_watch_time": (result['total_watch_time'] or 0) / max(result['total_views'] or 1, 1)
                        }
                    else:
                        return {
                            "user_id": user_id,
                            "total_videos_interacted": 0,
                            "videos_liked": 0,
                            "total_shares": 0,
                            "total_views": 0,
                            "total_watch_time": 0,
                            "average_watch_time": 0
                        }
                    
        except Exception as e:
            print(f"❌ Error getting user analytics: {e}")
            return {"error": str(e)}
    
    def get_video_comments(self, video_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video
        
        Args:
            video_id: Video identifier
            limit: Maximum number of comments to return
            
        Returns:
            List of comment dictionaries
        """
        try:
            # For now, return empty list since we don't have a comments table
            # In a full implementation, you'd query a comments table
            return []
            
        except Exception as e:
            print(f"❌ Error getting video comments: {e}")
            return []
    
    def _update_video_watch_analytics(self, video_id: str, watch_time: float):
        """Update video watch analytics"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if analytics record exists
                    cur.execute("""
                        SELECT video_id FROM analytics WHERE video_id = %s
                    """, (video_id,))
                    
                    if cur.fetchone():
                        # Update existing record
                        cur.execute("""
                            UPDATE analytics 
                            SET watch_count = watch_count + 1, 
                                total_watch_time = total_watch_time + %s
                            WHERE video_id = %s
                        """, (watch_time, video_id))
                    else:
                        # Create new record
                        cur.execute("""
                            INSERT INTO analytics (video_id, watch_count, total_watch_time, liked, share_count)
                            VALUES (%s, 1, %s, false, 0)
                        """, (video_id, watch_time))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ Error updating video watch analytics: {e}")
            raise
    
    def _update_video_like_count(self, video_id: str, increment: int):
        """Update video like count"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE videos 
                        SET like_count = like_count + %s
                        WHERE video_id = %s
                    """, (increment, video_id))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ Error updating video like count: {e}")
            raise
    
    def _update_video_share_count(self, video_id: str, increment: int):
        """Update video share count in both tables"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Update videos table
                    cur.execute("""
                        UPDATE videos 
                        SET share_count = share_count + %s
                        WHERE video_id = %s
                    """, (increment, video_id))
                    
                    # Update analytics table
                    cur.execute("""
                        UPDATE analytics 
                        SET share_count = share_count + %s
                        WHERE video_id = %s
                    """, (increment, video_id))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ Error updating video share count: {e}")
            raise 