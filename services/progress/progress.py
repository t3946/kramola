import time
from flask import current_app
import logging

PROGRESS_TTL = 60 * 60 * 24
PROGRESS_UPDATE_INTERVAL = 0.5  # Минимум 0.5 секунды между обновлениями (2 раза в секунду)


class Progress:
    def __init__(self, task_id: str, max_value: int = 100):
        self.task_id = task_id
        self.max_value = max_value
        self._pending_delta = 0  # Накопленные изменения для throttling
        self._last_update_time = 0  # Время последнего обновления
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        redis_client.hset(redis_key, "max_value", max_value)
        redis_client.expire(redis_key, PROGRESS_TTL)

    def _get_redis_key(self) -> str:
        """Get Redis key for this progress instance. Can be overridden in subclasses."""
        return f"task:{self.task_id}"

    def _flush_pending(self):
        """Применяет накопленные изменения в Redis (с throttling)"""
        if self._pending_delta == 0:
            return

        current_time = time.time()

        # Если прошло достаточно времени с последнего обновления (или это первое обновление), обновляем
        if self._last_update_time == 0 or current_time - self._last_update_time >= PROGRESS_UPDATE_INTERVAL:
            try:
                redis_client = current_app.redis_client_tasks
                redis_key = self._get_redis_key()
                redis_client.hincrbyfloat(redis_key, "progress", self._pending_delta)
                redis_client.expire(redis_key, PROGRESS_TTL)
                self._pending_delta = 0
                self._last_update_time = current_time

                # Отправляет событие прогресса через Socket.IO
                self._send_progress_event()
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logging.warning(f"Failed to update progress for task {self.task_id}: {e}")

    def _send_progress_event(self):
        """Отправляет событие прогресса через Socket.IO"""
        try:
            from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
            progress_value = self.getProgress()
            TaskProgressRoom.send_progress(self.task_id, progress_value)
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging
            logging.warning(f"Failed to send progress event for task {self.task_id}: {e}")

    def add(self, delta: float):
        """Add to current progress (with automatic throttling)"""
        self._pending_delta += delta
        self._flush_pending()

    def flush(self):
        """Принудительно применяет все накопленные изменения"""
        if self._pending_delta != 0:
            redis_client = current_app.redis_client_tasks
            redis_key = self._get_redis_key()
            redis_client.hincrbyfloat(redis_key, "progress", self._pending_delta)
            redis_client.expire(redis_key, PROGRESS_TTL)
            self._pending_delta = 0
            self._last_update_time = time.time()

            # Отправляем событие прогресса через Socket.IO
            self._send_progress_event()

    def setValue(self, value: float):
        logging.info("setValue")
        """Set progress value (bypasses throttling, applies immediately)"""
        # setValue применяется сразу, так как это установка конкретного значения, а не инкремент
        self._pending_delta = 0  # Сбрасываем накопленные изменения
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        redis_client.hset(redis_key, "progress", value)
        redis_client.expire(redis_key, PROGRESS_TTL)
        self._last_update_time = time.time()

        # Отправляем событие прогресса через Socket.IO
        self._send_progress_event()

    def getValue(self) -> float:
        """Get progress value"""
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        progress = redis_client.hget(redis_key, "progress")
        if progress:
            return float(progress.decode() if isinstance(progress, bytes) else progress)
        return 0.0

    def getProgress(self, decimals: int = 2) -> float:
        """Get progress percentage (0-100)
        
        Args:
            decimals (int): Number of decimal places (default: 2)
        
        Returns:
            float: Progress percentage from 0 to 100
        """
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        progress = redis_client.hget(redis_key, "progress")
        max_value = redis_client.hget(redis_key, "max_value")
        if progress and max_value:
            current = float(progress.decode() if isinstance(progress, bytes) else progress)
            max_val = float(max_value.decode() if isinstance(max_value, bytes) else max_value)
            percent = (current / max_val * 100) if max_val > 0 else 0.0
            return round(min(percent, 100.0), decimals)
        return 0.0

    def clear(self):
        """Clear progress"""
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        redis_client.hdel(redis_key, "progress")

    def drop(self):
        """Drop progress"""
        redis_client = current_app.redis_client_tasks
        redis_key = self._get_redis_key()
        redis_client.delete(redis_key)
