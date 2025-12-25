import time
from enum import Enum
from flask import current_app
from services.progress.progress import PROGRESS_TTL, PROGRESS_UPDATE_INTERVAL
from services.progress.docx.preparation_progress import PreparationProgress
from services.progress.docx.search_progress import SearchProgress


class ProgressType(Enum):
    """Type of progress to update."""
    PREPARATION = "preparation"
    SEARCH = "search"


class CombinedProgress:
    """Combines two progress trackers into one overall progress (50% each)."""

    def __init__(self, task_id: str, preparation_max_value: int, search_max_value: int):
        self.task_id = task_id
        self.preparation_progress = PreparationProgress(task_id, preparation_max_value)
        self.search_progress = SearchProgress(task_id, search_max_value)
        self._last_update_time = 0

        redis_client = current_app.redis_client_tasks
        redis_key = f"task:{self.task_id}"
        redis_client.hset(redis_key, "max_value", 100)
        redis_client.expire(redis_key, PROGRESS_TTL)

    def _update_combined_progress(self):
        """Update combined progress in Redis (50% preparation + 50% search)."""
        current_time = time.time()

        if self._last_update_time == 0 or current_time - self._last_update_time >= PROGRESS_UPDATE_INTERVAL:
            try:
                preparation_percent = self.preparation_progress.getProgress()
                search_percent = self.search_progress.getProgress()
                combined_percent = (preparation_percent * 0.5) + (search_percent * 0.5)

                redis_client = current_app.redis_client_tasks
                redis_key = f"task:{self.task_id}"
                redis_client.hset(redis_key, "progress", combined_percent)
                redis_client.expire(redis_key, PROGRESS_TTL)
                self._last_update_time = current_time

                self._send_progress_event(combined_percent)
            except Exception as e:
                import logging
                logging.warning(f"Failed to update combined progress for task {self.task_id}: {e}")

    def _send_progress_event(self, progress_value: float):
        """Send progress event through Socket.IO."""
        try:
            from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
            TaskProgressRoom.send_progress(self.task_id, progress_value)
        except Exception as e:
            import logging
            logging.warning(f"Failed to send progress event for task {self.task_id}: {e}")

    def add(self, delta: float, progress_type: ProgressType):
        """Add to progress.
        
        Args:
            delta (float): Value to add
            progress_type (ProgressType): Type of progress to update
        """
        if progress_type == ProgressType.PREPARATION:
            self.preparation_progress.add(delta)
        elif progress_type == ProgressType.SEARCH:
            self.search_progress.add(delta)

        self._update_combined_progress()

    def setValue(self, value: float, progress_type: ProgressType):
        """Set progress value.
        
        Args:
            value (float): Value to set
            progress_type (ProgressType): Type of progress to update
        """
        if progress_type == ProgressType.PREPARATION:
            self.preparation_progress.setValue(value)
        elif progress_type == ProgressType.SEARCH:
            self.search_progress.setValue(value)
        
        self._update_combined_progress()
    
    def setMax(self, max_value: int, progress_type: ProgressType):
        """Set maximum value for progress.
        
        Args:
            max_value (int): Maximum value to set
            progress_type (ProgressType): Type of progress to update
        """
        if progress_type == ProgressType.PREPARATION:
            self.preparation_progress.max_value = max_value
            redis_client = current_app.redis_client_tasks
            redis_key = self.preparation_progress._get_redis_key()
            redis_client.hset(redis_key, "max_value", max_value)
            redis_client.expire(redis_key, PROGRESS_TTL)
        elif progress_type == ProgressType.SEARCH:
            self.search_progress.max_value = max_value
            redis_client = current_app.redis_client_tasks
            redis_key = self.search_progress._get_redis_key()
            redis_client.hset(redis_key, "max_value", max_value)
            redis_client.expire(redis_key, PROGRESS_TTL)

    def flush(self):
        """Force flush all pending changes."""
        self.preparation_progress.flush()
        self.search_progress.flush()
        self._update_combined_progress()

    def getProgress(self, decimals: int = 2) -> float:
        """Get combined progress percentage (0-100).
        
        Args:
            decimals (int): Number of decimal places (default: 2)
        
        Returns:
            float: Combined progress percentage from 0 to 100
        """
        preparation_percent = self.preparation_progress.getProgress(decimals)
        search_percent = self.search_progress.getProgress(decimals)
        combined_percent = (preparation_percent * 0.5) + (search_percent * 0.5)
        return round(combined_percent, decimals)

    def clear(self):
        """Clear all progress."""
        self.preparation_progress.clear()
        self.search_progress.clear()
        redis_client = current_app.redis_client_tasks
        redis_key = f"task:{self.task_id}"
        redis_client.hdel(redis_key, "progress")

    def drop(self):
        """Drop all progress."""
        self.preparation_progress.drop()
        self.search_progress.drop()
        redis_client = current_app.redis_client_tasks
        redis_client.delete(f"task:{self.task_id}")
