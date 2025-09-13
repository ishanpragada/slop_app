#!/usr/bin/env python3
"""
Test script for UserPreferenceService
Tests all functionalities including database operations, preference calculations, and interaction tracking
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to the path so we can import the service
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.services.user_preference_service import UserPreferenceService

# Load environment variables
load_dotenv()

class TestUserPreferenceService:
    def __init__(self):
        self.service = UserPreferenceService()
        self.test_user_id = "test_user_123"
        self.test_video_ids = [
            "video_001", "video_002", "video_003", "video_004", "video_005",
            "video_006", "video_007", "video_008", "video_009", "video_010"
        ]
        
        # Mock the PineconeService to return fake embeddings
        self._mock_pinecone_service()
        
    def run_all_tests(self):
        """Run all test functions"""
        print("🧪 Starting UserPreferenceService Tests")
        print("=" * 60)
        
        tests = [
            self.test_database_connection,
            self.test_table_creation,
            self.test_interaction_weights,
            self.test_user_preference_creation,
            # self.test_store_interactions,
            self.test_preference_calculation,
            self.test_sliding_window,
            self.test_preference_update_threshold,
            self.test_get_user_preference,
            self.test_get_user_interactions,
            # self.test_cleanup
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                print(f"\n🔍 Running {test.__name__}...")
                test()
                print(f"✅ {test.__name__} PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ {test.__name__} FAILED: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        print("=" * 60)
        
        return failed == 0
    
    def _mock_pinecone_service(self):
        """Mock the PineconeService to return fake embeddings for testing"""
        def mock_get_video_embedding(video_id):
            # Return a fake 1536-dimensional embedding based on video_id
            import hashlib
            hash_obj = hashlib.md5(video_id.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            
            # Generate deterministic fake embedding
            embedding = []
            for i in range(1536):
                # Use hash and position to create deterministic values
                value = ((hash_int + i) % 1000) / 1000.0 - 0.5  # Values between -0.5 and 0.5
                embedding.append(value)
            
            return embedding
        
        # Replace the method in the service
        self.service.pinecone_service.get_video_embedding = mock_get_video_embedding
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            conn = self.service._get_connection()
            conn.close()
            print("   Database connection successful")
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    def test_table_creation(self):
        """Test that tables are created properly"""
        try:
            # This should not raise an exception
            self.service._initialize_database_tables()
            print("   Tables created/verified successfully")
        except Exception as e:
            raise Exception(f"Table creation failed: {e}")
    
    def test_interaction_weights(self):
        """Test interaction weight retrieval"""
        try:
            # Test all interaction types
            test_cases = [
                ("like", 1.0),
                ("save", 1.2),
                ("comment", 0.8),
                ("share", 0.9),
                ("view", 0.3),
                ("skip", -0.1),
                ("dislike", -0.5),
                ("unknown_type", 0.5)  # Default weight
            ]
            
            for interaction_type, expected_weight in test_cases:
                actual_weight = self.service._get_interaction_weight(interaction_type)
                if actual_weight != expected_weight:
                    raise Exception(f"Expected weight {expected_weight} for {interaction_type}, got {actual_weight}")
            
            print("   All interaction weights correct")
        except Exception as e:
            raise Exception(f"Interaction weight test failed: {e}")
    
    def test_user_preference_creation(self):
        """Test user preference creation"""
        try:
            # Clean up any existing test user
            self._cleanup_test_user()
            
            # Test creating new user preference
            self.service._create_user_preference(self.test_user_id)
            
            # Verify user preference exists
            if not self.service._user_preference_exists(self.test_user_id):
                raise Exception("User preference was not created")
            
            print("   User preference creation successful")
        except Exception as e:
            raise Exception(f"User preference creation failed: {e}")
    
    def test_store_interactions(self):
        """Test storing user interactions"""
        try:
            # Store multiple interactions using the full method (which increments counter)
            interaction_types = ["like", "view", "save", "comment", "share"]
            
            for i, interaction_type in enumerate(interaction_types):
                video_id = self.test_video_ids[i]
                
                # Use the full store_user_interaction method (includes counter logic)
                result = self.service.store_user_interaction(
                    self.test_user_id, 
                    video_id, 
                    interaction_type
                )
                
                if not result["success"]:
                    raise Exception(f"Failed to store interaction: {result.get('message', 'Unknown error')}")
                
                # Small delay to ensure different timestamps
                time.sleep(0.01)
            
            print("   Stored 5 interactions successfully")
        except Exception as e:
            raise Exception(f"Store interactions failed: {e}")
    
    def test_preference_calculation(self):
        """Test preference vector calculation"""
        try:
            # Calculate preference vector
            preference_vector = self.service._calculate_preference_vector(self.test_user_id)
            
            # Verify vector properties
            if not isinstance(preference_vector, list):
                raise Exception("Preference vector should be a list")
            
            if len(preference_vector) != 1536:
                raise Exception(f"Preference vector should have 1536 dimensions, got {len(preference_vector)}")
            
            # Check if vector is normalized (magnitude should be close to 1)
            magnitude = sum(x * x for x in preference_vector) ** 0.5
            if not (0.9 <= magnitude <= 1.1):
                raise Exception(f"Preference vector should be normalized, magnitude is {magnitude}")
            
            print(f"   Preference vector calculated successfully (magnitude: {magnitude:.3f})")
        except Exception as e:
            raise Exception(f"Preference calculation failed: {e}")
    
    def test_sliding_window(self):
        """Test sliding window functionality"""
        try:
            # Add more interactions to test sliding window
            for i in range(20):  # Add 20 more interactions (total will be 25)
                video_id = f"sliding_test_video_{i}"
                interaction_type = "view"
                
                # Use the full store_user_interaction method (includes counter logic)
                result = self.service.store_user_interaction(
                    self.test_user_id, 
                    video_id, 
                    interaction_type
                )
                
                if not result["success"]:
                    raise Exception(f"Failed to store interaction: {result.get('message', 'Unknown error')}")
                
                time.sleep(0.001)  # Small delay for different timestamps
            
            # Get user interactions (should only return last 20)
            interactions = self.service.get_user_interactions(self.test_user_id)
            
            if not interactions:
                raise Exception("No interactions returned")
            
            if len(interactions.interactions) > 20:
                raise Exception(f"Sliding window should limit to 20 interactions, got {len(interactions.interactions)}")
            
            print(f"   Sliding window working correctly (returned {len(interactions.interactions)} interactions)")
        except Exception as e:
            raise Exception(f"Sliding window test failed: {e}")
    
    def test_preference_update_threshold(self):
        """Test preference update threshold mechanism"""
        try:
            # Get current counter value
            current_counter = self.service._get_interactions_since_update(self.test_user_id)
            
            # Test that preference should not update when counter is below threshold
            should_update = self.service._should_update_preference(self.test_user_id)
            if should_update:
                raise Exception("Preference should not update when counter is below threshold")
            
            # Test the threshold logic by checking the method directly
            # We'll test with a hypothetical counter value of 15
            with self.service._get_connection() as conn:
                with conn.cursor() as cur:
                    # Temporarily set counter to 15 to test threshold logic
                    cur.execute(
                        "UPDATE user_preferences SET interactions_since_update = 15 WHERE user_uid = %s",
                        (self.test_user_id,)
                    )
                    conn.commit()
            
            # Test that preference should update when counter reaches threshold
            should_update = self.service._should_update_preference(self.test_user_id)
            if not should_update:
                raise Exception("Preference should update when counter reaches threshold")
            
            # Restore original counter value
            with self.service._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE user_preferences SET interactions_since_update = %s WHERE user_uid = %s",
                        (current_counter, self.test_user_id)
                    )
                    conn.commit()
            
            print("   Preference update threshold working correctly")
        except Exception as e:
            raise Exception(f"Preference update threshold test failed: {e}")
    
    
    def test_get_user_preference(self):
        """Test getting user preference"""
        try:
            # Get user preference
            preference = self.service.get_user_preference(self.test_user_id)
            
            if not preference:
                raise Exception("No user preference returned")
            
            # Verify preference properties
            if preference.user_id != self.test_user_id:
                raise Exception(f"Wrong user ID: expected {self.test_user_id}, got {preference.user_id}")
            
            if len(preference.preference_embedding) != 1536:
                raise Exception(f"Wrong embedding dimension: expected 1536, got {len(preference.preference_embedding)}")
            
            if preference.window_size != 20:
                raise Exception(f"Wrong window size: expected 20, got {preference.window_size}")
            
            print("   Get user preference successful")
        except Exception as e:
            raise Exception(f"Get user preference test failed: {e}")
    
    def test_get_user_interactions(self):
        """Test getting user interactions"""
        try:
            # Get user interactions
            interactions = self.service.get_user_interactions(self.test_user_id)
            
            if not interactions:
                raise Exception("No user interactions returned")
            
            # Verify interactions properties
            if interactions.user_id != self.test_user_id:
                raise Exception(f"Wrong user ID: expected {self.test_user_id}, got {interactions.user_id}")
            
            if len(interactions.interactions) == 0:
                raise Exception("No interactions in the window")
            
            # Verify interaction structure
            first_interaction = interactions.interactions[0]
            required_fields = ['video_id', 'embedding', 'type', 'weight', 'timestamp']
            for field in required_fields:
                if not hasattr(first_interaction, field):
                    raise Exception(f"Missing field in interaction: {field}")
            
            print(f"   Get user interactions successful ({len(interactions.interactions)} interactions)")
        except Exception as e:
            raise Exception(f"Get user interactions test failed: {e}")
    
    def test_cleanup(self):
        """Test cleanup functionality"""
        try:
            self._cleanup_test_user()
            print("   Cleanup successful")
        except Exception as e:
            raise Exception(f"Cleanup test failed: {e}")
    
    def _cleanup_test_user(self):
        """Clean up test user data"""
        try:
            with self.service._get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete user interactions
                    cur.execute("DELETE FROM user_interactions WHERE user_uid = %s", (self.test_user_id,))
                    
                    # Delete user preference
                    cur.execute("DELETE FROM user_preferences WHERE user_uid = %s", (self.test_user_id,))
                    
                    conn.commit()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

def main():
    """Main test function"""
    print("🚀 UserPreferenceService Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app/services/user_preference_service.py"):
        print("❌ Error: Please run this test from the backend directory")
        return False
    
    # Run tests
    tester = TestUserPreferenceService()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n💥 Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
