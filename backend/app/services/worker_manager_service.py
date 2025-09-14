import os
import subprocess
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from app.services.redis_service import RedisService

class WorkerManagerService:
    """Service for managing and monitoring background video workers"""
    
    def __init__(self):
        load_dotenv()
        self.redis_service = RedisService()
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all registered workers"""
        try:
            client = self.redis_service.get_client()
            workers_data = client.hgetall("video_workers")
            
            workers = []
            for worker_id, worker_info_str in workers_data.items():
                try:
                    # Parse worker info (stored as string representation of dict)
                    worker_info = eval(worker_info_str)  # Safe since we control the data
                    workers.append({
                        "worker_id": worker_id,
                        "info": worker_info,
                        "status": "active"  # If registered in Redis, it's active
                    })
                except Exception as e:
                    print(f"⚠️  Error parsing worker info for {worker_id}: {e}")
            
            return {
                "success": True,
                "total_workers": len(workers),
                "workers": workers,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_workers": 0,
                "workers": []
            }
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about all video generation queues"""
        try:
            client = self.redis_service.get_client()
            queue_keys = client.keys("video_queue:*")
            
            total_queues = len(queue_keys)
            total_pending = 0
            total_ready = 0
            total_in_progress = 0
            
            queue_details = []
            
            for queue_key in queue_keys:
                user_id = queue_key.replace("video_queue:", "")
                queue_items = client.zrevrange(queue_key, 0, -1)
                
                pending = 0
                ready = 0
                in_progress = 0
                
                for item_json in queue_items:
                    try:
                        item = json.loads(item_json)
                        item_type = item.get("type", "unknown")
                        status = item.get("status", "unknown")
                        
                        if item_type == "generate_video":
                            if status == "pending_generation":
                                pending += 1
                            elif status == "in_progress":
                                in_progress += 1
                        elif item_type == "existing_video":
                            ready += 1
                            
                    except json.JSONDecodeError:
                        continue
                
                if pending > 0 or ready > 0 or in_progress > 0:
                    queue_details.append({
                        "user_id": user_id,
                        "pending": pending,
                        "ready": ready,
                        "in_progress": in_progress,
                        "total": pending + ready + in_progress
                    })
                
                total_pending += pending
                total_ready += ready
                total_in_progress += in_progress
            
            return {
                "success": True,
                "summary": {
                    "total_queues": total_queues,
                    "active_queues": len(queue_details),
                    "total_pending": total_pending,
                    "total_ready": total_ready,
                    "total_in_progress": total_in_progress,
                    "total_items": total_pending + total_ready + total_in_progress
                },
                "queue_details": queue_details,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {},
                "queue_details": []
            }
    
    def start_worker(self, background: bool = True) -> Dict[str, Any]:
        """Start a new background video worker"""
        try:
            # Path to the worker script
            worker_script = os.path.join(
                os.path.dirname(__file__), 
                "background_video_worker.py"
            )
            
            if not os.path.exists(worker_script):
                return {
                    "success": False,
                    "error": f"Worker script not found: {worker_script}"
                }
            
            if background:
                # Start worker in background
                process = subprocess.Popen(
                    ["python", worker_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(os.path.dirname(worker_script))  # Backend root
                )
                
                return {
                    "success": True,
                    "message": "Background worker started",
                    "pid": process.pid,
                    "background": True
                }
            else:
                # Start worker in foreground (for testing)
                return {
                    "success": True,
                    "message": "Run 'python app/services/background_video_worker.py' to start worker",
                    "background": False,
                    "command": f"python {worker_script}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start worker"
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health for video generation"""
        try:
            worker_status = self.get_worker_status()
            queue_stats = self.get_queue_statistics()
            
            # Determine health status
            health_status = "healthy"
            issues = []
            
            # Check if workers are running
            if worker_status["total_workers"] == 0:
                health_status = "warning"
                issues.append("No active workers found")
            
            # Check for large backlogs
            if queue_stats.get("summary", {}).get("total_pending", 0) > 50:
                health_status = "warning"
                issues.append("Large backlog of pending video generations")
            
            # Check Redis connectivity
            try:
                self.redis_service.get_client().ping()
                redis_status = "connected"
            except Exception:
                redis_status = "disconnected"
                health_status = "critical"
                issues.append("Redis connection failed")
            
            return {
                "success": True,
                "health_status": health_status,
                "issues": issues,
                "components": {
                    "redis": redis_status,
                    "workers": {
                        "status": "active" if worker_status["total_workers"] > 0 else "inactive",
                        "count": worker_status["total_workers"]
                    },
                    "queues": {
                        "active_queues": queue_stats.get("summary", {}).get("active_queues", 0),
                        "pending_tasks": queue_stats.get("summary", {}).get("total_pending", 0),
                        "in_progress_tasks": queue_stats.get("summary", {}).get("total_in_progress", 0)
                    }
                },
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "health_status": "critical",
                "issues": [f"Health check failed: {str(e)}"]
            }
    
    def clear_stale_workers(self) -> Dict[str, Any]:
        """Clear worker registrations that are no longer active"""
        try:
            client = self.redis_service.get_client()
            workers_data = client.hgetall("video_workers")
            
            cleared_count = 0
            active_count = 0
            
            for worker_id, worker_info_str in workers_data.items():
                try:
                    worker_info = eval(worker_info_str)
                    pid = worker_info.get("pid")
                    
                    # Check if process is still running
                    if pid and not self._is_process_running(pid):
                        client.hdel("video_workers", worker_id)
                        cleared_count += 1
                        print(f"🧹 Cleared stale worker: {worker_id} (PID: {pid})")
                    else:
                        active_count += 1
                        
                except Exception as e:
                    # If we can't parse the worker info, clear it
                    client.hdel("video_workers", worker_id)
                    cleared_count += 1
                    print(f"🧹 Cleared malformed worker entry: {worker_id}")
            
            return {
                "success": True,
                "cleared_workers": cleared_count,
                "active_workers": active_count,
                "message": f"Cleared {cleared_count} stale worker registrations"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to clear stale workers"
            }
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is still running"""
        try:
            os.kill(pid, 0)  # Send signal 0 to check if process exists
            return True
        except OSError:
            return False

    def get_worker_logs(self, lines: int = 50) -> Dict[str, Any]:
        """Get recent worker logs (if available)"""
        # This would need to be implemented based on your logging setup
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Worker logs not implemented yet",
            "logs": [
                "Worker logs would appear here",
                "Implement based on your logging infrastructure"
            ]
        }
