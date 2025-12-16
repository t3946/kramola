from flask import current_app

PROGRESS_TTL = 60 * 60 * 24

class Progress:
    def __init__(self, task_id, max_value=100):
        self.task_id = task_id
        self.max_value = max_value
        redis_client = current_app.redis_client_tasks
        redis_client.hset(f"task:{self.task_id}", "max_value", max_value)
        redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
    
    def add(self, delta):
        """Add to current progress"""
        redis_client = current_app.redis_client_tasks
        redis_client.hincrbyfloat(f"task:{self.task_id}", "progress", delta)
        redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
    
    def setValue(self, value):
        """Set progress value"""
        redis_client = current_app.redis_client_tasks
        redis_client.hset(f"task:{self.task_id}", "progress", value)
        redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
    
    def getValue(self):
        """Get progress value"""
        redis_client = current_app.redis_client_tasks
        progress = redis_client.hget(f"task:{self.task_id}", "progress")
        if progress:
            return float(progress.decode() if isinstance(progress, bytes) else progress)
        return 0.0
    
    def getProgress(self, decimals=2):
        """Get progress percentage (0-100)
        
        Args:
            decimals (int): Number of decimal places (default: 2)
        
        Returns:
            float: Progress percentage from 0 to 100
        """
        redis_client = current_app.redis_client_tasks
        progress = redis_client.hget(f"task:{self.task_id}", "progress")
        max_value = redis_client.hget(f"task:{self.task_id}", "max_value")
        if progress and max_value:
            current = float(progress.decode() if isinstance(progress, bytes) else progress)
            max_val = float(max_value.decode() if isinstance(max_value, bytes) else max_value)
            percent = (current / max_val * 100) if max_val > 0 else 0.0
            return round(min(percent, 100.0), decimals)
        return 0.0
    
    def clear(self):
        """Clear progress"""
        redis_client = current_app.redis_client_tasks
        redis_client.hdel(f"task:{self.task_id}", "progress")
    
    def drop(self):
        """Drop progress"""
        redis_client = current_app.redis_client_tasks
        redis_client.delete(f"task:{self.task_id}")
