import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pinecone import Pinecone

class PineconeService:
    def __init__(self):
        load_dotenv()
        
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Index name for Slop videos
        self.index_name = "slop-videos"
        
        # Initialize or get existing index
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize Pinecone index with integrated embeddings if it doesn't exist"""
        try:
            # Check if index exists
            if not self.pc.has_index(self.index_name):
                # Create new index with integrated embeddings
                self.pc.create_index_for_model(
                    name=self.index_name,
                    cloud="aws",
                    region="us-east-1",
                    embed={
                        "model": "llama-text-embed-v2",
                        "field_map": {"text": "prompt"}
                    }
                )
                print(f"✅ Created new Pinecone index with integrated embeddings: {self.index_name}")
            else:
                print(f"✅ Using existing Pinecone index: {self.index_name}")
                
        except Exception as e:
            print(f"❌ Error initializing Pinecone index: {e}")
            raise
    
    def add_prompt_embedding(
        self, 
        prompt: str, 
        video_id: str, 
        s3_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a prompt embedding to Pinecone using integrated embeddings
        
        Args:
            prompt: The prompt text to embed
            video_id: Unique video identifier
            s3_url: Optional S3 URL for the video
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Get the index
            index = self.pc.Index(self.index_name)
            
            # Upsert with integrated embeddings using the correct API format
            # For now, let's keep it simple without metadata to test the basic functionality
            records = [{
                "_id": video_id,
                "prompt": prompt  # This will be automatically embedded (matches field_map)
            }]
            
            index.upsert_records("ns1", records)
            
            print(f"✅ Added embedding for video {video_id} to Pinecone")
            
            return {
                "success": True,
                "video_id": video_id,
                "index_name": self.index_name,
                "prompt": prompt
            }
            
        except Exception as e:
            print(f"❌ Error adding embedding to Pinecone: {e}")
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }
    
    def find_similar_prompts(
        self, 
        query_prompt: str, 
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar prompts using vector similarity with integrated embeddings
        
        Args:
            query_prompt: The prompt to find similar ones for
            k: Number of similar prompts to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar prompts with metadata and embeddings
        """
        try:
            # Get the index
            index = self.pc.Index(self.index_name)
            
            # Perform semantic search with integrated embeddings
            results = index.search(
                namespace="ns1",
                query={
                    "inputs": {"text": query_prompt},
                    "top_k": k
                },
                fields=["prompt"],
                include_vectors=True  # Include actual embedding vectors
            )
            
            # Format results
            similar_prompts = []
            for hit in results.result.hits:
                similar_prompts.append({
                    "prompt": hit.fields.get("prompt", ""),
                    "similarity_score": hit._score,
                    "video_id": hit._id,
                    "embedding": hit.vector,  # Include the actual embedding vector
                    "metadata": {
                        "video_id": hit._id,
                        "score": hit._score,
                        "fields": hit.fields
                    }
                })
            
            print(f"✅ Found {len(similar_prompts)} similar prompts with embeddings")
            return similar_prompts
            
        except Exception as e:
            print(f"❌ Error finding similar prompts: {e}")
            return []
    
    def get_video_embedding(self, video_id: str) -> Optional[List[float]]:
        """
        Get the embedding vector for a specific video
        
        Args:
            video_id: The video ID to get embedding for
            
        Returns:
            Embedding vector (1536 dimensions) or None if not found
        """
        try:
            # Get the index
            index = self.pc.Index(self.index_name)
            
            # Fetch the vector by ID
            results = index.fetch(ids=[video_id], namespace="ns1")
            
            if results.vectors and video_id in results.vectors:
                vector = results.vectors[video_id]
                print(f"✅ Retrieved embedding for video {video_id}")
                
                # Extract the actual embedding values from the Vector object
                # The Vector object has a 'values' attribute that contains the embedding
                if hasattr(vector, 'values'):
                    embedding_values = vector.values
                    if isinstance(embedding_values, list):
                        return embedding_values
                    else:
                        # Convert to list if it's not already
                        return list(embedding_values)
                else:
                    # Fallback: try to access the vector directly
                    # This handles different Pinecone API versions
                    try:
                        # Try to convert the vector to a list
                        if hasattr(vector, '__iter__'):
                            return list(vector)
                        else:
                            print(f"❌ Unexpected vector format for video {video_id}")
                            return None
                    except Exception as e:
                        print(f"❌ Error converting vector to list: {e}")
                        return None
            else:
                print(f"❌ Video {video_id} not found in index")
                return None
                
        except Exception as e:
            print(f"❌ Error getting video embedding: {e}")
            return None
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            return {
                "index_name": self.index_name,
                "total_vector_count": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "metric": stats.get("metric", ""),
                "namespaces": stats.get("namespaces", {})
            }
            
        except Exception as e:
            print(f"❌ Error getting index stats: {e}")
            return {"error": str(e)}
    
    def delete_video_embedding(self, video_id: str) -> Dict[str, Any]:
        """
        Delete a video embedding from Pinecone
        
        Args:
            video_id: The video ID to delete
            
        Returns:
            Dictionary with operation result
        """
        try:
            index = self.pc.Index(self.index_name)
            
            # Delete by ID
            index.delete(ids=[video_id], namespace="ns1")
            
            print(f"✅ Deleted embedding for video {video_id}")
            
            return {
                "success": True,
                "video_id": video_id,
                "message": "Embedding deleted successfully"
            }
            
        except Exception as e:
            print(f"❌ Error deleting embedding: {e}")
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }