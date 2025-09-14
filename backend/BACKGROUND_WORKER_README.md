# 🤖 Background Video Worker System

A comprehensive background processing system for automatic video generation based on user preferences.

## 🏗️ System Architecture

```
User Interactions → Preference Updates → Queue Creation → Background Worker → Video Generation
```

### Components

1. **VideoGenerationQueueService** - Creates and manages video generation queues
2. **BackgroundVideoWorker** - Processes queued tasks and generates videos
3. **WorkerManagerService** - Monitors and manages worker instances
4. **API Endpoints** - RESTful interface for worker management

## 🚀 Quick Start

### 1. Process Pending Tasks Immediately

```bash
# Process all pending tasks until queues are empty
python process_video_queue.py

# Via API (if server is running)
curl -X POST http://localhost:8000/workers/process-all-pending
```

### 2. Start a Continuous Background Worker

```bash
# Simple start
python start_video_worker.py

# Background start with logging
nohup python start_video_worker.py > worker.log 2>&1 &

# Via API (if server is running)
curl -X POST http://localhost:8000/workers/start
```

### 2. Monitor Worker Status

```bash
# Check system health
curl http://localhost:8000/workers/health

# Get worker status
curl http://localhost:8000/workers/status

# Queue statistics
curl http://localhost:8000/workers/queue-stats
```

### 3. Test the System

```bash
python test_background_worker.py
```

## 🔄 How It Works

### Automatic Trigger Flow

1. **User Interaction** → User likes/views/saves videos
2. **Preference Update** → After 15 interactions, preference vector updates
3. **Queue Creation** → `VideoGenerationQueueService` automatically creates queue
4. **Strategy Decision**:
   - **≥3 similar videos found** → Add existing videos to queue
   - **<3 similar videos found** → Generate new prompts using LLM
5. **Background Processing** → Worker picks up tasks and generates videos
6. **Video Storage** → Generated videos saved to S3 and PostgreSQL

### Queue Item Types

```json
{
  "type": "existing_video",
  "status": "ready",
  "video_id": "uuid",
  "s3_url": "https://...",
  "similarity_score": 0.85
}
```

```json
{
  "type": "generate_video", 
  "status": "pending_generation",
  "prompt": "A cinematic shot of...",
  "preference_vector": [1536 floats],
  "priority": 3
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Worker Configuration
WORKER_POLL_INTERVAL=30          # Seconds between queue checks
MAX_CONCURRENT_GENERATIONS=2     # Max parallel video generations
GENERATION_TIMEOUT=300           # 5 minutes timeout per video

# Queue Configuration  
SIMILARITY_THRESHOLD=15          # Very permissive similarity matching
PREFERENCE_UPDATE_THRESHOLD=15   # Interactions before preference update

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Service Configuration

```python
# In background_video_worker.py
self.poll_interval = 30           # How often to check for tasks
self.max_concurrent_generations = 2  # Parallel generation limit
self.generation_timeout = 300     # Task timeout in seconds
```

## 📊 Monitoring & Management

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workers/status` | GET | Get active worker status |
| `/workers/health` | GET | System health check |
| `/workers/queue-stats` | GET | Queue statistics |
| `/workers/start` | POST | Start new worker |
| `/workers/clear-stale` | POST | Clean up inactive workers |
| `/workers/logs` | GET | Get worker logs |

### Health Status Indicators

- **🟢 Healthy** - Workers active, queues processing normally
- **🟡 Warning** - No workers running or large backlogs
- **🔴 Critical** - Redis connection failed or system errors

### Queue Statistics

```json
{
  "summary": {
    "total_queues": 15,
    "active_queues": 8,
    "total_pending": 12,
    "total_ready": 45,
    "total_in_progress": 3
  }
}
```

## 🛠️ Worker Management

### Starting Workers

```python
# Programmatic start
from app.services.worker_manager_service import WorkerManagerService

manager = WorkerManagerService()
result = manager.start_worker(background=True)
```

### Scaling Workers

- **Single Worker**: Good for development and light load
- **Multiple Workers**: Each worker can handle 2 concurrent generations
- **Horizontal Scaling**: Run workers on different machines/containers

### Worker Lifecycle

1. **Registration** - Worker registers in Redis on startup
2. **Task Processing** - Continuously polls queues for work
3. **Generation** - Uses VideoGenerationService for actual video creation
4. **Completion** - Updates queue with generated video metadata
5. **Cleanup** - Graceful shutdown on SIGINT/SIGTERM

## 🔧 Troubleshooting

### Common Issues

**No videos being generated:**
```bash
# Check if workers are running
curl http://localhost:8000/workers/status

# Check queue has pending tasks
curl http://localhost:8000/workers/queue-stats

# Start a worker if none running
python start_video_worker.py
```

**Workers stuck or hanging:**
```bash
# Clear stale worker registrations
curl -X POST http://localhost:8000/workers/clear-stale

# Check system health
curl http://localhost:8000/workers/health
```

**Queue not being created:**
```bash
# Verify user has 15+ interactions
# Check preference update logs
# Ensure Redis is running
```

### Debug Mode

```python
# Enable verbose logging in worker
import logging
logging.basicConfig(level=logging.DEBUG)

# Test queue creation manually
from app.services.video_generation_queue_service import VideoGenerationQueueService
queue_service = VideoGenerationQueueService()
result = queue_service.process_new_preference_vector(user_id, preference_vector)
```

### Performance Tuning

```bash
# Increase concurrent generations
export MAX_CONCURRENT_GENERATIONS=4

# Decrease poll interval for faster processing
export WORKER_POLL_INTERVAL=10

# Increase timeout for complex videos
export GENERATION_TIMEOUT=600
```

## 📝 Logging

Worker logs include:
- Task start/completion times
- Video generation results
- Error details and stack traces
- Queue statistics
- Performance metrics

```bash
# View real-time logs
tail -f worker.log

# Search for errors
grep "❌" worker.log

# Find successful generations
grep "✅ Video generation completed" worker.log
```

## 🔄 Integration Points

### User Preference Service
- Automatically triggers queue creation
- Provides preference vectors for personalization

### Video Generation Service
- Handles actual video creation using Veo 3 Fast
- Manages S3 upload and storage

### Database Services
- PostgreSQL for video metadata
- Redis for queue management
- Pinecone for similarity search

### AWS Services
- S3 for video storage
- Potential for SQS/Lambda integration

## 🚧 Future Enhancements

- **Auto-scaling** based on queue depth
- **Priority queues** for premium users
- **Batch processing** for efficiency
- **Webhook notifications** on completion
- **Metrics dashboard** for monitoring
- **Retry logic** for failed generations
- **Load balancing** across workers

## 📊 Example Usage

```python
# Complete workflow example
from app.services.user_preference_service import UserPreferenceService

# Create user interactions (triggers automatic queue creation)
preference_service = UserPreferenceService()

for i in range(15):  # Trigger preference update
    preference_service.store_user_interaction(
        user_id="user123",
        video_id=f"video_{i}",
        interaction_type="like"
    )

# Background worker automatically processes the queue
# Generated videos appear in user's personalized feed
```

The system provides a complete automated pipeline from user interactions to personalized video generation, with robust monitoring and management capabilities.
