from flask_socketio import emit, join_room, leave_room
from flask import current_app

from blueprints.tool_highlight.redis_tasks import get_redis_tasks_client

class TaskProgressRoom:
    """Room for task progress updates"""
    
    ROOM_PREFIX = "task_progress:"
    
    @staticmethod
    def get_room_name(task_id):
        """Get room name for task_id"""
        return f"{TaskProgressRoom.ROOM_PREFIX}{task_id}"
    
    @staticmethod
    def on_join(data):
        from services.progress.task_progress import TaskProgress

        """Handle client joining progress room"""
        task_id = data.get('task_id')
        room_name = TaskProgressRoom.get_room_name(task_id)
        join_room(room_name)
        
        progress = TaskProgress(task_id)
        emit('progress', {'task_id': task_id, 'progress': progress.getProgress()})
        emit('joined', {'task_id': task_id})
        
        redis_client = get_redis_tasks_client()
        if redis_client:
            try:
                raw_redis_data = redis_client.hgetall(f"task:{task_id}")
                if raw_redis_data:
                    state = raw_redis_data.get(b'state') or raw_redis_data.get('state')
                    status_message = raw_redis_data.get(b'status_message') or raw_redis_data.get('status_message')
                    
                    if state:
                        state_str = state.decode() if isinstance(state, bytes) else state
                        status_str = status_message.decode() if isinstance(status_message, bytes) else (status_message or '')
                        emit('task_status', {
                            'task_id': task_id,
                            'state': state_str,
                            'status': status_str
                        })
            except Exception as e:
                current_app.logger.warning(f"Failed to send initial status for task {task_id}: {e}")
    
    @staticmethod
    def on_leave(data):
        """Handle client leaving progress room"""
        task_id = data.get('task_id')
        leave_room(TaskProgressRoom.get_room_name(task_id))
    
    @staticmethod
    def send_progress(task_id, progress_value=None):
        """Send progress update to room"""
        socketio = current_app.extensions.get('socketio')
        socketio.emit('progress', {
            'task_id': task_id,
            'progress': progress_value
        }, room=TaskProgressRoom.get_room_name(task_id))
    
    @staticmethod
    def send_status(task_id, state, status_message):
        """Send task status update to room"""
        socketio = current_app.extensions.get('socketio')
        socketio.emit('task_status', {
            'task_id': task_id,
            'state': state,
            'status': status_message
        }, room=TaskProgressRoom.get_room_name(task_id))
