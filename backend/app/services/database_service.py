import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseService:
    def __init__(self):
        load_dotenv()
        
        # Database connection parameters
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Initialize database tables
        self._initialize_database_tables()
    
    def _get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            raise
    
    def _initialize_database_tables(self):
        """Create the required database tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Create videos table
                    create_videos_table_sql = """
                    CREATE TABLE IF NOT EXISTS videos (
                        video_id VARCHAR(255) PRIMARY KEY,
                        s3_url VARCHAR(500) NOT NULL,
                        prompt TEXT NOT NULL,
                        length_seconds INTEGER NOT NULL DEFAULT 8,
                        caption TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        like_count INTEGER DEFAULT 0,
                        share_count INTEGER DEFAULT 0
                    );
                    """
                    
                    # Create analytics table if not exists
                    create_analytics_table_sql = """
                    CREATE TABLE IF NOT EXISTS analytics (
                        id SERIAL PRIMARY KEY,
                        video_id VARCHAR(255) NOT NULL,
                        watch_count INTEGER DEFAULT 0,
                        total_watch_time FLOAT DEFAULT 0,
                        liked BOOLEAN DEFAULT FALSE,
                        share_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
                    );
                    """
                    
                    # Create indexes for performance
                    create_indexes_sql = [
                        "CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_videos_like_count ON videos(like_count DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_analytics_video_id ON analytics(video_id);"
                    ]
                    
                    cur.execute(create_videos_table_sql)
                    print("✅ Videos table created/verified")
                    
                    cur.execute(create_analytics_table_sql)
                    print("✅ Analytics table created/verified")
                    
                    for index_sql in create_indexes_sql:
                        cur.execute(index_sql)
                    print("✅ Database indexes created/verified")
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ Error initializing database tables: {e}")
            raise
    
    def save_video_metadata(
        self,
        video_id: str,
        s3_url: str,
        prompt: str,
        length_seconds: int = 8,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save video metadata to PostgreSQL videos table
        
        Args:
            video_id: Unique video identifier
            s3_url: S3 URL where the video is stored
            prompt: Text prompt used to generate the video
            length_seconds: Video duration in seconds (default: 8)
            caption: Optional video caption/description
            
        Returns:
            Dictionary with operation result
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Insert video metadata
                    insert_sql = """
                    INSERT INTO videos (video_id, s3_url, prompt, length_seconds, caption, created_at, like_count, share_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (video_id) DO UPDATE SET
                        s3_url = EXCLUDED.s3_url,
                        prompt = EXCLUDED.prompt,
                        length_seconds = EXCLUDED.length_seconds,
                        caption = EXCLUDED.caption
                    """
                    
                    current_time = datetime.now()
                    cur.execute(insert_sql, (
                        video_id,
                        s3_url,
                        prompt,
                        length_seconds,
                        caption,
                        current_time,
                        0,  # Initial like_count
                        0   # Initial share_count
                    ))
                    
                    conn.commit()
                    
                    print(f"✅ Video metadata saved to PostgreSQL: {video_id}")
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "message": "Video metadata saved successfully to PostgreSQL"
                    }
                    
        except Exception as e:
            print(f"❌ Error saving video metadata to PostgreSQL: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save video metadata to PostgreSQL"
            }
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata from PostgreSQL by video_id
        
        Args:
            video_id: Video identifier
            
        Returns:
            Dictionary with video data or None if not found
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT video_id, s3_url, prompt, length_seconds, caption, 
                               created_at, like_count, share_count
                        FROM videos 
                        WHERE video_id = %s
                    """, (video_id,))
                    
                    result = cur.fetchone()
                    
                    if result:
                        return dict(result)
                    else:
                        return None
                        
        except Exception as e:
            print(f"❌ Error getting video by ID: {e}")
            return None
    
    def update_video_stats(
        self,
        video_id: str,
        like_count_increment: int = 0,
        share_count_increment: int = 0
    ) -> Dict[str, Any]:
        """
        Update video statistics (like count, share count)
        
        Args:
            video_id: Video identifier
            like_count_increment: Amount to increment like count by
            share_count_increment: Amount to increment share count by
            
        Returns:
            Dictionary with operation result
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    update_sql = """
                    UPDATE videos 
                    SET like_count = like_count + %s,
                        share_count = share_count + %s
                    WHERE video_id = %s
                    """
                    
                    cur.execute(update_sql, (like_count_increment, share_count_increment, video_id))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        return {
                            "success": True,
                            "message": f"Video stats updated for {video_id}"
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Video {video_id} not found"
                        }
                        
        except Exception as e:
            print(f"❌ Error updating video stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update video stats"
            }
    
    def list_videos(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List videos from PostgreSQL with pagination
        
        Args:
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            
        Returns:
            Dictionary with videos list and pagination info
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get videos with pagination
                    cur.execute("""
                        SELECT video_id, s3_url, prompt, length_seconds, caption, 
                               created_at, like_count, share_count
                        FROM videos 
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    videos = [dict(row) for row in cur.fetchall()]
                    
                    # Get total count
                    cur.execute("SELECT COUNT(*) FROM videos")
                    total_count = cur.fetchone()[0]
                    
                    return {
                        "success": True,
                        "videos": videos,
                        "total_count": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_more": (offset + limit) < total_count
                    }
                    
        except Exception as e:
            print(f"❌ Error listing videos: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to list videos"
            }
