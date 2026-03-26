from flask import current_app


def get_redis_tasks_client():
    if hasattr(current_app, 'redis_client_tasks') and current_app.redis_client_tasks:
        return current_app.redis_client_tasks

    current_app.logger.warning(
        "Redis client 'redis_client_tasks' not found in current_app. Task persistence to Redis disabled.")

    return None
