#!/usr/bin/env python3
"""
Script to process all pending video generation tasks until queues are empty
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from app.services.background_video_worker import BackgroundVideoWorker

def main():
    print("🎬 Processing All Pending Video Generation Tasks")
    print("=" * 60)
    print("This will process all queued video generation tasks until")
    print("all queues are empty, then exit.")
    print("-" * 60)
    
    worker = BackgroundVideoWorker()
    
    try:
        # Set worker as running
        worker.running = True
        from datetime import datetime
        worker.stats["started_at"] = datetime.now().isoformat()
        
        # Process all pending tasks
        total_processed = worker.process_all_pending_tasks()
        
        print(f"\n🎉 Successfully processed {total_processed} video generation tasks!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        worker.stop()
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        worker.running = False
        print("✅ Task processing completed")

if __name__ == "__main__":
    main()
