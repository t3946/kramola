from services.progress.task_progress import TaskProgress


class PreparationProgress(TaskProgress):
    """Progress tracker for document preparation phase (building dictionary and filtering phrases)."""
    
    def _get_redis_key(self) -> str:
        """Get Redis key with preparation suffix."""
        return f"task:{self.task_id}:preparation"
    
    def _send_progress_event(self):
        """Override to disable socket events - CombinedProgress handles them."""
        pass

