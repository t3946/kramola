from services.progress.progress import Progress


class SearchProgress(Progress):
    """Progress tracker for search phase (analyzing paragraphs and tables)."""
    
    def _get_redis_key(self) -> str:
        """Get Redis key with search suffix."""
        return f"task:{self.task_id}:search"
    
    def _send_progress_event(self):
        """Override to disable socket events - CombinedProgress handles them."""
        pass

