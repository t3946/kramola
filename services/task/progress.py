import time
from flask import current_app

PROGRESS_TTL = 60 * 60 * 24
PROGRESS_UPDATE_INTERVAL = 0.5  # Минимум 0.5 секунды между обновлениями (2 раза в секунду)

class Progress:
    def __init__(self, task_id, max_value=100):
        self.task_id = task_id
        self.max_value = max_value
        self._pending_delta = 0  # Накопленные изменения для throttling
        self._last_update_time = 0  # Время последнего обновления
        redis_client = current_app.redis_client_tasks
        redis_client.hset(f"task:{self.task_id}", "max_value", max_value)
        redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
    
    def _flush_pending(self):
        """Применяет накопленные изменения в Redis (с throttling)"""
        if self._pending_delta == 0:
            return
        
        current_time = time.time()
        
        # Если прошло достаточно времени с последнего обновления (или это первое обновление), обновляем
        if self._last_update_time == 0 or current_time - self._last_update_time >= PROGRESS_UPDATE_INTERVAL:
            try:
                redis_client = current_app.redis_client_tasks
                redis_client.hincrbyfloat(f"task:{self.task_id}", "progress", self._pending_delta)
                redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
                self._pending_delta = 0
                self._last_update_time = current_time
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logging.warning(f"Failed to update progress for task {self.task_id}: {e}")
    
    def add(self, delta):
        """Add to current progress (with automatic throttling)"""
        self._pending_delta += delta
        self._flush_pending()
    
    def flush(self):
        """Принудительно применяет все накопленные изменения"""
        if self._pending_delta != 0:
            redis_client = current_app.redis_client_tasks
            redis_client.hincrbyfloat(f"task:{self.task_id}", "progress", self._pending_delta)
            redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
            self._pending_delta = 0
            self._last_update_time = time.time()

    def setValue(self, value):
        """Set progress value (bypasses throttling, applies immediately)"""
        # setValue применяется сразу, так как это установка конкретного значения, а не инкремент
        self._pending_delta = 0  # Сбрасываем накопленные изменения
        redis_client = current_app.redis_client_tasks
        redis_client.hset(f"task:{self.task_id}", "progress", value)
        redis_client.expire(f"task:{self.task_id}", PROGRESS_TTL)
        self._last_update_time = time.time()
    
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
