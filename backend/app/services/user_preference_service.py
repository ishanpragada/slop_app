import os
import math
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from app.models.analytics_models import UserInteraction, UserInteractionWindow, UserPreference
from app.services.pinecone_service import PineconeService

class UserPreferenceService:
    def __init__(self):
        load_dotenv()
        
        # Configuration
        self.preference_update_threshold = int(os.getenv("PREFERENCE_UPDATE_THRESHOLD", 15))
        self.window_size = 20
        
        # Interaction weights
        self.interaction_weights = {
            "like": 1.0,      # Full influence
            "save": 1.2,      # Stronger than like
            "comment": 0.8,   # Good influence
            "share": 0.9,     # Strong influence
            "view": 0.3,      # Weak influence
            "skip": -0.3,     # Slight negative influence
            "dislike": -0.5   # Negative influence
        }
        
        # Database connection parameters
        # self.db_config = {
        #     'host': os.getenv('DB_HOST', 'slop-instance-1.cdqmssqmipy3.us-east-2.rds.amazonaws.com'),
        #     'database': os.getenv('DB_NAME', 'postgres'),
        #     'user': os.getenv('DB_USER', 'slop'),
        #     'password': os.getenv('DB_PASSWORD', 'SlopDatabase123'),
        #     'port': os.getenv('DB_PORT', '5432')
        # }

        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Initialize database tables
        self._initialize_database_tables()
        
        # Initialize Pinecone service
        self.pinecone_service = PineconeService()
    
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
                    # Create user_preferences table
                    create_preferences_table_sql = """
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        user_uid VARCHAR(255) PRIMARY KEY,
                        preference_vector JSONB NOT NULL,
                        window_size INTEGER DEFAULT 20,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        interactions_since_update INTEGER DEFAULT 0,
                        preference_update_threshold INTEGER DEFAULT 15
                    );
                    """
                    
                    # Create user_interactions table
                    create_interactions_table_sql = """
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id SERIAL PRIMARY KEY,
                        user_uid VARCHAR(255) NOT NULL,
                        video_id VARCHAR(255) NOT NULL,
                        interaction_type VARCHAR(50) NOT NULL,
                        weight FLOAT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        embedding JSONB NOT NULL,
                        FOREIGN KEY (user_uid) REFERENCES user_preferences(user_uid) ON DELETE CASCADE
                    );
                    """
                    
                    # Create indexes for performance
                    create_indexes_sql = [
                        "CREATE INDEX IF NOT EXISTS idx_user_interactions_user_uid_timestamp ON user_interactions(user_uid, timestamp DESC);",
                        "CREATE INDEX IF NOT EXISTS idx_user_interactions_user_uid ON user_interactions(user_uid);"
                    ]
                    
                    cur.execute(create_preferences_table_sql)
                    cur.execute(create_interactions_table_sql)
                    
                    # Create indexes
                    for index_sql in create_indexes_sql:
                        cur.execute(index_sql)
                    
                    conn.commit()
                    print("✅ Database tables created/verified successfully")
                    
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            raise
    
    def store_user_interaction(
        self, 
        user_id: str, 
        video_id: str, 
        interaction_type: str
    ) -> Dict[str, Any]:
        """
        Store a user interaction and conditionally update preferences
        
        Args:
            user_id: Unique user identifier (Firebase UID)
            video_id: Video identifier
            interaction_type: Type of interaction
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Extract original video ID if it has infinite feed suffixes
            original_video_id = self._extract_original_video_id(video_id)
            
            # Get video embedding from Pinecone using the original video ID
            video_embedding = self.pinecone_service.get_video_embedding(original_video_id)
            
            if not video_embedding:
                return {
                    "success": False,
                    "error": f"Video {original_video_id} not found in Pinecone index",
                    "message": "Failed to retrieve video embedding"
                }
            
            # Ensure user preference exists before storing interaction
            if not self._user_preference_exists(user_id):
                self._create_user_preference(user_id)
            
            # Get interaction weight from database
            weight = self._get_interaction_weight(interaction_type)
            
            # Store interaction in database
            self._store_interaction(user_id, video_id, interaction_type, weight, video_embedding)
            
            # Check if preference should be updated
            should_update = self._should_update_preference(user_id)
            
            if should_update:
                # Recalculate preference vector
                new_preference = self._calculate_preference_vector(user_id)
                self._save_user_preference(user_id, new_preference)
                
                # Reset counter to 1
                self._reset_interaction_counter(user_id)
                
                return {
                    "success": True,
                    "message": f"Interaction stored and preference updated",
                    "preference_updated": True,
                    "interactions_since_update": 1
                }
            else:
                # Increment the counter
                self._increment_interaction_counter(user_id)
                
                return {
                    "success": True,
                    "message": f"Interaction stored (preference update pending)",
                    "preference_updated": False,
                    "interactions_since_update": self._get_interactions_since_update(user_id)
                }
                
        except Exception as e:
            print(f"❌ Error storing user interaction: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to store user interaction"
            }
    
    def _user_preference_exists(self, user_id: str) -> bool:
        """Check if user preference exists in database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM user_preferences WHERE user_uid = %s",
                        (user_id,)
                    )
                    return cur.fetchone() is not None
        except Exception as e:
            print(f"❌ Error checking user preference existence: {e}")
            return False
    
    def _create_user_preference(self, user_id: str):
        """Create a new user preference record in database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    default_vector = self._get_default_preference()
                    
                    cur.execute("""
                        INSERT INTO user_preferences (user_uid, preference_vector, window_size, interactions_since_update, preference_update_threshold)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, json.dumps(default_vector), self.window_size, 0, self.preference_update_threshold))
                    
                    conn.commit()
                    print(f"✅ Created user preference for user: {user_id}")
                    
        except Exception as e:
            print(f"❌ Error creating user preference: {e}")
            raise
    
    def _get_interaction_weight(self, interaction_type: str) -> float:
        """Get interaction weight from hardcoded values"""
        return self.interaction_weights.get(interaction_type, 0.5)  # Default weight
    
    def _extract_original_video_id(self, video_id: str) -> str:
        """
        Extract the original video ID from infinite feed unique IDs
        
        Args:
            video_id: Video ID that may have infinite feed suffixes like :33:198
            
        Returns:
            Original video ID without suffixes
        """
        # If the video ID contains colons, it's likely an infinite feed unique ID
        # Format: original_video_id:round_number:position
        if ':' in video_id:
            # Split by colon and take the first part (original video ID)
            original_id = video_id.split(':')[0]
            print(f"Extracted original video ID: {original_id} from unique ID: {video_id}")
            return original_id
        
        # If no colons, it's already the original video ID
        return video_id
    
    def _store_interaction(self, user_id: str, video_id: str, interaction_type: str, weight: float, embedding: List[float]):
        """Store a new interaction in the database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_interactions (user_uid, video_id, interaction_type, weight, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, video_id, interaction_type, weight, json.dumps(embedding)))
                    
                    conn.commit()
                    
        except Exception as e:
            print(f"❌ Error storing interaction: {e}")
            raise
    
    def _should_update_preference(self, user_id: str) -> bool:
        """Check if preference vector should be updated"""
        if not self._user_preference_exists(user_id):
            return True  # New user, always update
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT interactions_since_update, preference_update_threshold FROM user_preferences WHERE user_uid = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    if not result:
                        return True
                    
                    interactions_since_update, threshold = result
                    return interactions_since_update >= threshold
        except Exception as e:
            print(f"❌ Error checking if should update preference: {e}")
            return True
    
    def _get_user_preference_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preference from database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT preference_vector, window_size, last_updated, interactions_since_update FROM user_preferences WHERE user_uid = %s",
                        (user_id,)
                    )
                    
                    result = cur.fetchone()
                    if result:
                        return {
                            "vector": result['preference_vector'],
                            "window_size": result['window_size'],
                            "last_updated": result['last_updated'].isoformat() if result['last_updated'] else None,
                            "interactions_since_update": result['interactions_since_update']
                        }
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting user preference from database: {e}")
            return None
    
    def _calculate_preference_vector(self, user_id: str) -> List[float]:
        """Calculate preference vector from sliding window interactions"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Get the last 20 interactions for this user
                    cur.execute("""
                        SELECT embedding, weight 
                        FROM user_interactions 
                        WHERE user_uid = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (user_id, self.window_size))
                    
                    interactions = cur.fetchall()
                    
                    if not interactions:
                        return self._get_default_preference()
                    
                    # Get dimension from first interaction
                    first_embedding = interactions[0][0]  # JSONB field
                    dimension = len(first_embedding)
                    
                    # Initialize weighted sum
                    weighted_sum = [0.0] * dimension
                    total_weight = 0.0
                    
                    # Calculate weighted average
                    for embedding, weight in interactions:
                        for i in range(dimension):
                            weighted_sum[i] += embedding[i] * weight
                        
                        total_weight += weight
                    
                    # Calculate average
                    if total_weight > 0:
                        preference_vector = [weighted_sum[i] / total_weight for i in range(dimension)]
                    else:
                        preference_vector = self._get_default_preference()
                    
                    # L2 normalize
                    return self._l2_normalize(preference_vector)
                    
        except Exception as e:
            print(f"❌ Error calculating preference vector: {e}")
            return self._get_default_preference()
    
    def _l2_normalize(self, vector: List[float]) -> List[float]:
        """L2 normalize a vector"""
        magnitude = math.sqrt(sum(x * x for x in vector))
        
        if magnitude == 0:
            return vector
        
        return [x / magnitude for x in vector]
    
    def _get_default_preference(self) -> List[float]:
        """Get default preference vector (neutral)"""
        # Return a neutral vector (all zeros) - 1536 dimensions
        return [0.0] * 1536
    
    def _save_user_preference(self, user_id: str, preference_vector: List[float]):
        """Save user preference vector to database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_preferences 
                        SET preference_vector = %s, last_updated = CURRENT_TIMESTAMP
                        WHERE user_uid = %s
                    """, (json.dumps(preference_vector), user_id))
                    
                    conn.commit()
                    print(f"✅ Updated user preference for user: {user_id}")
                    
        except Exception as e:
            print(f"❌ Error saving user preference: {e}")
            raise
    
    def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        """Get user's current preference vector from database"""
        try:
            preference_data = self._get_user_preference_from_db(user_id)
            if not preference_data:
                return None
            
            return UserPreference(
                user_id=user_id,
                preference_embedding=preference_data.get("vector", []),
                window_size=preference_data.get("window_size", self.window_size),
                last_updated=preference_data.get("last_updated", ""),
                interactions_since_update=preference_data.get("interactions_since_update", 0)
            )
            
        except Exception as e:
            print(f"❌ Error getting user preference: {e}")
            return None
    
    def get_user_interactions(self, user_id: str) -> Optional[UserInteractionWindow]:
        """Get user's current interaction window from database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT video_id, embedding, interaction_type, weight, timestamp
                        FROM user_interactions 
                        WHERE user_uid = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, (user_id, self.window_size))
                    
                    interactions_data = cur.fetchall()
                    if not interactions_data:
                        return None
                    
                    interactions = []
                    
                    for video_id, embedding, interaction_type, weight, timestamp in interactions_data:
                        interaction = UserInteraction(
                            video_id=video_id,
                            embedding=embedding,
                            type=interaction_type,
                            weight=weight,
                            timestamp=timestamp.isoformat()
                        )
                        interactions.append(interaction)
                    
                    return UserInteractionWindow(
                        user_id=user_id,
                        interactions=interactions,
                        last_updated=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            print(f"❌ Error getting user interactions: {e}")
            return None
    
    def _get_interactions_since_update(self, user_id: str) -> int:
        """Get number of interactions since last preference update"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT interactions_since_update FROM user_preferences WHERE user_uid = %s",
                        (user_id,)
                    )
                    result = cur.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            print(f"❌ Error getting interactions since update: {e}")
            return 0
    
    def _increment_interaction_counter(self, user_id: str):
        """Increment the interaction counter for a user in database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_preferences 
                        SET interactions_since_update = interactions_since_update + 1
                        WHERE user_uid = %s
                    """, (user_id,))
                    
                    conn.commit()
                        
        except Exception as e:
            print(f"❌ Error incrementing interaction counter: {e}")
    
    def _reset_interaction_counter(self, user_id: str):
        """Reset the interaction counter for a user in database"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE user_preferences 
                        SET interactions_since_update = 1
                        WHERE user_uid = %s
                    """, (user_id,))
                    
                    conn.commit()
                        
        except Exception as e:
            print(f"❌ Error resetting interaction counter: {e}")
    