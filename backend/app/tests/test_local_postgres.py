#!/usr/bin/env python3
"""
Test script to connect to AWS PostgreSQL database and insert sample user preference data
"""

import psycopg2
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST', 'slop-instance-1.cdqmssqmipy3.us-east-2.rds.amazonaws.com'),
#     'database': os.getenv('DB_NAME', 'postgres'),
#     'user': os.getenv('DB_USERNAME'),
#     'password': os.getenv('DB_PASSWORD'),
#     'port': int(os.getenv('DB_PORT', 5432))
# }

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'slop'),  # Changed from DB_USERNAME
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}


def create_connection():
    """Create a connection to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def create_user_preferences_table(conn):
    """Create the user_preferences table if it doesn't exist"""
    try:
        cursor = conn.cursor()
        
        # Create table with proper constraints
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_uid VARCHAR(255) PRIMARY KEY,
            preference_embedding JSONB NOT NULL
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ User preferences table created/verified successfully")
        cursor.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating table: {e}")
        conn.rollback()

def insert_sample_user_preference(conn):
    """Insert a sample user preference record"""
    try:
        cursor = conn.cursor()
        
        # Sample data
        sample_user_uid = "sammy_test_2"
        sample_preference_embedding = {
            "vector": [0.1, 0.2, 0.3, 0.4, 0.5] + [0.0] * 1531,  # 1536 dimensions
            "metadata": {
                "window_size": 20,
                "last_updated": "2024-01-15T10:30:00Z",
                "interactions_since_update": 0,
                "total_interactions": 5
            }
        }
        
        # Insert query
        insert_sql = """
        INSERT INTO user_preferences (user_uid, preference_embedding)
        VALUES (%s, %s)
        ON CONFLICT (user_uid) 
        DO UPDATE SET 
            preference_embedding = EXCLUDED.preference_embedding
        RETURNING user_uid;
        """
        
        cursor.execute(insert_sql, (sample_user_uid, json.dumps(sample_preference_embedding)))
        
        # Get the inserted/updated record
        result = cursor.fetchone()
        if result:
            user_uid = result[0]
            print(f"✅ Successfully inserted/updated user preference for: {user_uid}")
        
        conn.commit()
        cursor.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error inserting sample data: {e}")
        conn.rollback()

def query_user_preferences(conn):
    """Query and display user preferences"""
    try:
        cursor = conn.cursor()
        
        # Query all user preferences
        query_sql = "SELECT user_uid, preference_embedding FROM user_preferences;"
        cursor.execute(query_sql)
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n📊 Found {len(results)} user preference(s):")
            print("=" * 80)
            
            for row in results:
                user_uid, preference_embedding = row
                print(f"User UID: {user_uid}")
                
                # Parse and display preference embedding info
                if isinstance(preference_embedding, str):
                    pref_data = json.loads(preference_embedding)
                else:
                    pref_data = preference_embedding
                
                if 'vector' in pref_data:
                    vector = pref_data['vector']
                    print(f"Vector dimensions: {len(vector)}")
                    print(f"Vector preview: {vector[:5]}...")
                
                if 'metadata' in pref_data:
                    metadata = pref_data['metadata']
                    print(f"Window size: {metadata.get('window_size', 'N/A')}")
                    print(f"Total interactions: {metadata.get('total_interactions', 'N/A')}")
                
                print("-" * 80)
        else:
            print("📭 No user preferences found in the database")
        
        cursor.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error querying data: {e}")

def main():
    """Main function to test database operations"""
    print("🚀 AWS PostgreSQL Database Test")
    print("=" * 50)
    
    # Create connection
    conn = create_connection()
    if not conn:
        print("❌ Failed to connect to database. Exiting.")
        return
    
    try:
        # Create table if it doesn't exist
        create_user_preferences_table(conn)
        
        # Insert sample data
        insert_sample_user_preference(conn)
        
        # Query and display results
        query_user_preferences(conn)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        # Close connection
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main() 