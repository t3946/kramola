from .rooms.task_progress import TaskProgressRoom

def register_socketio_handlers(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('join_task_progress')
    def handle_join_task_progress(data):
        """Handle join_task_progress event"""
        TaskProgressRoom.on_join(data)
    
    @socketio.on('leave_task_progress')
    def handle_leave_task_progress(data):
        """Handle leave_task_progress event"""
        TaskProgressRoom.on_leave(data)
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        from flask import current_app
        current_app.logger.debug('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        from flask import current_app
        current_app.logger.debug('Client disconnected')
