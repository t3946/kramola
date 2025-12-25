# task_status route

import json
from flask import current_app, jsonify
from services.task.result import TaskResult
from services.task import TaskStatus

from ..routes import (
    highlight_bp,
    _get_redis_client,
    _EXECUTOR_FUTURES_REGISTRY,
    REDIS_TASK_TTL
)


@highlight_bp.route('/task_status/<task_id>', methods=['GET'])
def check_task_status(task_id):
    logger = current_app.logger
    redis_client = _get_redis_client()
    task_info_from_redis_initial = None

    try:
        raw_redis_data = redis_client.hgetall(f"task:{task_id}")

        if raw_redis_data:
            task_info_from_redis_initial = {k: v for k, v in raw_redis_data.items()}  # Ensure mutable copy
    except Exception as e_redis_get:
        logger.error(f"Task {task_id}: Redis error getting initial task status: {e_redis_get}", exc_info=True)
        # Continue, will rely on future or ultimately fail if Redis is persistently down

    active_future = _EXECUTOR_FUTURES_REGISTRY.get(task_id)

    if active_future:
        if active_future.running():
            if task_info_from_redis_initial and task_info_from_redis_initial.get('state') == TaskStatus.PENDING.value:
                try:
                    redis_client.hmset(f"task:{task_id}",
                                       {"state": TaskStatus.PROCESSING.value, "status_message": "Задача выполняется..."})
                    redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                    
                    from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
                    TaskProgressRoom.send_status(task_id, TaskStatus.PROCESSING.value, "Задача выполняется...")
                except Exception as e_redis_run:
                    logger.error(f"Task {task_id}: Redis error updating to PROCESSING: {e_redis_run}")
            elif not task_info_from_redis_initial:
                logger.warning(
                    f"Task {task_id} running, but no initial Redis record. Background task should create it.")
            return jsonify({'state': TaskStatus.PROCESSING.value, 'status': 'Задача выполняется...'})

        elif active_future.done():
            logger.info(f"Task {task_id} future is done. Removing from registry.")
            # We get the future object itself before removing its key from the registry,
            # so we can call .result() on it later if needed.
            # _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None) is done after handling result.

            result_data = TaskResult.load(task_id)
            if result_data:
                state_val = task_info_from_redis_initial.get("state") if task_info_from_redis_initial else redis_client.hget(f"task:{task_id}", "state")
                status_val = task_info_from_redis_initial.get("status_message") if task_info_from_redis_initial else redis_client.hget(f"task:{task_id}", "status_message")
                state = (state_val.decode() if isinstance(state_val, bytes) else state_val) or TaskStatus.UNKNOWN.value
                status_msg = (status_val.decode() if isinstance(status_val, bytes) else status_val) or "Статус из Redis"
                logger.info(f"Task {task_id} result successfully retrieved from Redis. State: {state}")
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)
                return jsonify({
                    'state': state,
                    'status': status_msg
                })
            
            logger.warning(f"Task {task_id}: Attempting to get result from future.result() as Redis fallback.")
            try:
                result_from_future = active_future.result()
                TaskResult.save(task_id, result_from_future)
                is_error = bool(result_from_future.get('error'))
                final_status_msg = result_from_future.get('error') or 'Задача завершена (результат из future).'
                logger.info(f"Task {task_id} obtained result directly from future. Error: {is_error}")
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)
                return jsonify({
                    'state': TaskStatus.FAILURE.value if is_error else TaskStatus.SUCCESS.value,
                    'status': final_status_msg
                })
            except Exception as e_future_res_direct:
                logger.error(f"Task {task_id} critical error: future.result() failed: {e_future_res_direct}",
                             exc_info=True)
                critical_error_msg = 'Критическая ошибка: результат задачи не может быть получен.'
                error_data = {'error': critical_error_msg, '_task_id_ref': task_id}
                TaskResult.save(task_id, error_data)
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)
                return jsonify({
                    'state': TaskStatus.FAILURE.value,
                    'status': critical_error_msg
                })

    if task_info_from_redis_initial:
        state = task_info_from_redis_initial.get("state", TaskStatus.UNKNOWN.value)
        status_msg = task_info_from_redis_initial.get("status_message", "Статус из Redis")
        return jsonify({
            'state': state.decode() if isinstance(state, bytes) else state,
            'status': status_msg.decode() if isinstance(status_msg, bytes) else status_msg
        })

    logger.warning(f"Task {task_id} not found in active futures or Redis (final check).")
    return jsonify({'state': TaskStatus.NOT_FOUND.value, 'status': 'Задача не найдена или информация о ней утеряна.'}), 404

