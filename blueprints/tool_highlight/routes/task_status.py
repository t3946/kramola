# task_status route

import json
from flask import current_app, session, jsonify

# Импортируем highlight_bp и вспомогательные функции из основного файла routes.py
from ..routes import (
    highlight_bp,
    _get_redis_client,
    _EXECUTOR_FUTURES_REGISTRY,
    REDIS_TASK_TTL
)


@highlight_bp.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
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
            if redis_client and task_info_from_redis_initial and task_info_from_redis_initial.get('state') == 'PENDING':
                try:
                    redis_client.hmset(f"task:{task_id}",
                                       {"state": "PROCESSING", "status_message": "Задача выполняется..."})
                    redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                except Exception as e_redis_run:
                    logger.error(f"Task {task_id}: Redis error updating to PROCESSING: {e_redis_run}")
            elif redis_client and not task_info_from_redis_initial:  # Future running but no Redis record yet
                logger.warning(
                    f"Task {task_id} running, but no initial Redis record. Background task should create it.")
            return jsonify({'state': 'PROCESSING', 'status': 'Задача выполняется...'})

        elif active_future.done():
            logger.info(f"Task {task_id} future is done. Removing from registry.")
            # We get the future object itself before removing its key from the registry,
            # so we can call .result() on it later if needed.
            # _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None) is done after handling result.

            # Try to get final result from Redis first
            if redis_client:
                raw_redis_data_final = redis_client.hgetall(f"task:{task_id}")
                if raw_redis_data_final and 'result_data_json' in raw_redis_data_final:
                    try:
                        deserialized_data = json.loads(raw_redis_data_final['result_data_json'])
                        session['last_result_data_highlight'] = deserialized_data
                        state = raw_redis_data_final.get("state", "UNKNOWN")
                        status_msg = raw_redis_data_final.get("status_message", "Статус из Redis")
                        logger.info(f"Task {task_id} result successfully retrieved from Redis. State: {state}")
                        _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)  # Clean up
                        return jsonify({'state': state, 'status': status_msg, 'result_data_for_session': True})
                    except json.JSONDecodeError:
                        logger.error(
                            f"Task {task_id}: Could not decode result_data_json from Redis: {raw_redis_data_final['result_data_json']}")
                        # Fall through to future.result()
                else:
                    logger.warning(
                        f"Task {task_id}: Future done, but no final/complete record in Redis. Will try future.result().")

            # If not successfully retrieved from Redis (or Redis client is None)
            logger.warning(f"Task {task_id}: Attempting to get result from future.result() as Redis fallback.")
            try:
                # The 'active_future' variable holds the future object.
                result_from_future = active_future.result()
                session['last_result_data_highlight'] = result_from_future
                is_error = bool(result_from_future.get('error'))
                final_status_msg = result_from_future.get('error') or 'Задача завершена (результат из future).'
                logger.info(f"Task {task_id} obtained result directly from future. Error: {is_error}")
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)  # Clean up
                return jsonify({
                    'state': 'FAILURE' if is_error else 'SUCCESS',
                    'status': final_status_msg,
                    'result_data_for_session': True
                })
            except Exception as e_future_res_direct:
                logger.error(f"Task {task_id} critical error: future.result() failed: {e_future_res_direct}",
                             exc_info=True)
                critical_error_msg = 'Критическая ошибка: результат задачи не может быть получен.'
                session['last_result_data_highlight'] = {'error': critical_error_msg, '_task_id_ref': task_id}
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None)  # Clean up
                return jsonify({'state': 'FAILURE', 'status': critical_error_msg, 'result_data_for_session': True})

    # If future is not in registry (e.g., already processed and popped, or app restarted)
    # Rely solely on Redis if available and had initial info.
    if task_info_from_redis_initial:  # From the very first Redis check
        state = task_info_from_redis_initial.get("state", "UNKNOWN")
        status_msg = task_info_from_redis_initial.get("status_message", "Статус из Redis")
        # If result_data_json is present, it means task completed and Redis has it.
        if 'result_data_json' in task_info_from_redis_initial:
            try:
                session['last_result_data_highlight'] = json.loads(task_info_from_redis_initial['result_data_json'])
                return jsonify({'state': state, 'status': status_msg,
                                'result_data_for_session': (state in ["SUCCESS", "FAILURE"])})
            except json.JSONDecodeError:
                logger.error(f"Task {task_id}: Could not decode result_data_json from task_info_from_redis_initial.")
                # Fall through to NOT_FOUND or treat as error
        else:  # No final result in Redis, but an initial record existed (e.g. PENDING, PROCESSING)
            logger.warning(
                f"Task {task_id} not in active futures. Initial Redis state was '{state}'. Final result missing.")
            # This could mean the task is still genuinely processing by a worker, but this status check lost track of the live future.
            # Or it failed and Redis didn't get updated.
            # Returning current (possibly non-final) state. Client will continue polling.
            return jsonify({'state': state, 'status': status_msg, 'result_data_for_session': False})

    logger.warning(f"Task {task_id} not found in active futures or Redis (final check).")
    return jsonify({'state': 'NOT_FOUND', 'status': 'Задача не найдена или информация о ней утеряна.'}), 404

