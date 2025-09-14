# API Endpoints Documentation

## Base URL
- Local Development: `http://localhost:8000/api/v1`

## Health Check Endpoints

### GET `/`
Root endpoint
- **Response**: `{"message": "Welcome to Slop API"}`

### GET `/health`
Health check endpoint
- **Response**: `{"status": "healthy"}`

### GET `/hello`
Simple test endpoint
- **Response**: `{"message": "Hello from FastAPI!"}`

## Video Upload & Management Endpoints

### POST `/videos/upload`
Upload a video to S3
- **Body**: 
  - `file`: Video file (multipart/form-data)
  - `metadata`: Optional JSON string containing video metadata
- **Response**: Video ID, URLs, and metadata

### GET `/videos/{video_id}`
Retrieve a specific video by ID
- **Parameters**: `video_id` - UUID string with or without .mp4 extension
- **Response**: Video stream (media type based on content)

### GET `/videos/{video_id}/info`
Get video information without downloading the actual video data
- **Parameters**: `video_id` - Video ID
- **Response**: Video metadata and information

### GET `/videos/{video_id}/url`
Get the public URL for a video
- **Parameters**: `video_id` - Video ID
- **Response**: Public video URL

### GET `/videos`
List all videos in the S3 bucket
- **Query Parameters**: 
  - `prefix`: S3 key prefix to filter by (default: "videos/")
  - `max_keys`: Maximum number of videos to return (default: 100)
- **Response**: List of videos with metadata

### GET `/videos/{video_id}/exists`
Check if a video exists in S3
- **Parameters**: `video_id` - Video ID
- **Response**: Boolean indicating existence


### DELETE `/videos/{video_id}`
Delete a video and its associated metadata
- **Parameters**: `video_id` - Video ID
- **Response**: Deletion confirmation

## AI Prompt Generation Endpoints

### POST `/ai/prompts/generate`
Generate a detailed prompt for Veo 2 video generation
- **Body**: 
```json
{
  "base_topic": "string (optional)"
}
```
- **Response**: 
```json
{
  "success": true,
  "prompt": {
    "prompt": "Detailed cinematic prompt for Veo 2",
    "base_topic": "Original topic used",
    "style": "Visual style applied",
    "camera_movement": "Camera technique used",
    "lighting": "Lighting style",
    "category": "Content category",
    "generation_method": "Method used"
  },
  "message": "Prompt generated successfully"
}
```

### GET `/ai/prompts/random`
Generate a random detailed prompt for Veo 2 video generation
- **Response**: 
```json
{
  "success": true,
  "prompt": {
    "prompt": "Detailed cinematic prompt for Veo 2",
    "base_topic": "Random topic generated",
    "style": "Visual style applied",
    "camera_movement": "Camera technique used",
    "lighting": "Lighting style",
    "category": "Content category",
    "generation_method": "Method used"
  },
  "message": "Prompt generated successfully"
}
```

## Analytics Endpoints

### POST `/analytics/interaction`
Track a user interaction with a video
- **Body**: 
```json
{
  "user_id": "string",
  "video_id": "string",
  "action": "string (like, comment, share, save, view)",
  "timestamp": "string (optional, ISO format)",
  "metadata": "object (optional)"
}
```
- **Response**: 
```json
  {
  "success": true,
  "message": "Successfully tracked like interaction",
  "interaction_id": "uuid",
  "timestamp": "2024-07-27T16:30:00"
}
```

### POST `/analytics/comment`
Add a comment to a video
- **Body**: 
```json
{
  "user_id": "string",
  "video_id": "string",
  "comment_text": "string (max 1000 characters)",
  "timestamp": "string (optional, ISO format)"
}
```
- **Response**: 
```json
{
  "success": true,
  "message": "Comment added successfully",
  "interaction_id": "uuid",
  "timestamp": "2024-07-27T16:30:00"
}
```

### GET `/analytics/video/{video_id}`
Get analytics for a specific video
- **Parameters**: `video_id` - Video identifier
- **Response**: 
```json
  {
  "video_id": "string",
  "total_views": 0,
  "total_likes": 0,
  "total_shares": 0,
  "total_saves": 0,
  "total_comments": 0,
  "average_watch_time": null,
  "engagement_rate": null
  }
```

### GET `/analytics/user/{user_id}`
Get analytics for a specific user
- **Parameters**: `user_id` - User identifier
- **Response**: 
```json
{
  "user_id": "string",
  "total_interactions": 0,
  "videos_liked": 0,
  "videos_commented": 0,
  "videos_shared": 0,
  "videos_saved": 0,
  "average_watch_time": null
}
```

### GET `/analytics/video/{video_id}/comments`
Get comments for a specific video
- **Parameters**: 
  - `video_id` - Video identifier
  - `limit` - Maximum number of comments (default: 50)
- **Response**: 
```json
{
  "success": true,
  "video_id": "string",
  "comments": [
    {
      "comment_id": "uuid",
      "user_id": "string",
      "video_id": "string",
      "comment_text": "string",
      "timestamp": "2024-07-27T16:30:00"
    }
  ],
  "total_comments": 0
}
```
    "prompt": "Random detailed cinematic prompt",
    "base_topic": "Auto-generated topic",
    "style": "Visual style applied",
    "camera_movement": "Camera technique used",
    "lighting": "Lighting style",
    "category": "Content category",
    "generation_method": "Method used"
  },
  "message": "Random prompt generated successfully"
}
```

## AI Video Generation Endpoints

### POST `/ai/videos/generate`
Start AI video generation using Google's Veo 2 API
- **Body**: 
```json
{
    "prompt": "string (required)",
    "aspect_ratio": "string (optional, default: '16:9')",
    "duration_seconds": "integer (optional, default: 8, fixed at 8 for Veo 3 Fast)",
    "number_of_videos": "integer (optional, default: 1)"
  }
  ```
- **Response**: 
```json
{
    "success": true,
    "operation_id": "uuid",
    "google_operation_id": "google_operation_id",
    "status": "generating",
    "prompt": "prompt_text",
    "settings": {
      "aspect_ratio": "16:9",
      "duration_seconds": 8,
      "number_of_videos": 1
    },
    "created_at": 1234567890.123,
    "message": "Video generation started. Use the operation_id to check status."
  }
```

### GET `/ai/videos/status/{google_operation_id}`
Check the status of an AI video generation operation
- **Parameters**: `google_operation_id` - Google's operation ID from generate endpoint
- **Response**: 
```json
{
    "google_operation_id": "operation_id",
    "status": "generating|completed",
    "done": false,
    "video_uri": "google_video_url (if complete)",
    "video_id": "generated_video_id (if complete)",
    "generation_complete": false
}
```

### GET `/ai/videos/wait/{google_operation_id}`
Wait for video generation to complete (blocking call)
- **Parameters**: 
  - `google_operation_id` - Google's operation ID
  - `max_wait_seconds` - Maximum time to wait (query param, default: 300)
- **Response**: 
```json
{
  "success": true,
    "google_operation_id": "operation_id",
    "status": "completed",
    "video_uri": "google_video_url",
    "video_id": "generated_video_id",
    "metadata": {
      "google_uri": "google_video_url",
      "generation_complete": true,
      "note": "Veo 2 videos are silent (no audio generation)"
    },
    "message": "Video generation completed successfully"
}
```

### POST `/ai/videos/download/{google_operation_id}`
Download the generated video and optionally save to S3
- **Parameters**: 
  - `google_operation_id` - Google's operation ID
- **Response**: 
```json
{
  "success": true,
    "google_operation_id": "operation_id",
    "video_uri": "google_video_url",
    "download_complete": true,
    "saved_to_postgres": true,
    "postgres_video_id": "video_id"
}
```

### GET `/ai/videos/metadata/{google_operation_id}`
Get comprehensive metadata for an AI-generated video
- **Parameters**: `google_operation_id` - Google's operation ID
- **Response**: 
```json
{
    "google_operation_id": "operation_id",
    "generation_status": "completed",
    "model": "veo-2.0-generate-001",
    "video_uri": "google_video_url",
    "video_id": "generated_video_id",
    "generation_details": {
      "model_name": "Google Veo 2",
      "generation_type": "text_to_video",
      "has_audio": false,
      "note": "Veo 2 videos are silent - for audio, use Veo 3 Fast"
    },
    "urls": {
      "google_direct_url": "google_video_url",
      "expiration_note": "Google URL will expire after some time"
    }
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors, invalid parameters)
- `404`: Not Found (video/resource not found)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing the issue"
}
```

## Environment Variables

Required environment variables:
- `GEMINI_API_KEY`: Google GenAI API key for Veo video generation (video generation only)
- `CLAUDE_API_KEY`: Anthropic Claude API key for text generation and prompt enhancement
- AWS credentials for S3 operations (configured via aws_service.py)

## Notes

1. **Veo 2 Limitations**: 
   - Duration must be between 5-8 seconds
   - Videos are generated without audio
   - For audio generation, use Veo 3 Fast model

2. **Video Generation Workflow**:
   1. Call `/ai/videos/generate` to start generation
   2. Use returned `google_operation_id` to check status with `/ai/videos/status/{id}`
   3. Once complete, optionally download with `/ai/videos/download/{id}`
   4. Get comprehensive metadata with `/ai/videos/metadata/{id}`

3. **Google URLs**: 
   - Direct Google video URLs are temporary and will expire
   - Download and save to S3 for permanent storage

4. **S3 Integration**: 
   - Generated videos can be automatically saved to S3
   - Metadata is stored separately for easy retrieval 