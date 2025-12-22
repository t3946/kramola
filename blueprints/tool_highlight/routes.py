# tool_highlight/routes.py

import os
import time
import traceback
import uuid
import json  # Для сериализации/десериализации данных в Redis
from collections import Counter
from typing import List

from services.analyser import AnalyseData, AnalyserDocx


from flask import (
    request, redirect, url_for, Blueprint, current_app, render_template,
    session, send_file, jsonify
)

from services.highlight_upload import (
    HighlightUploadService, UploadError
)
from services.pymorphy_service import (
    prepare_search_terms,
    get_highlight_search_data,
    get_highlight_phrase_map,
    reset_caches
)
from services.highlight_service import (
    analyze_and_highlight_docx, analyze_and_highlight_pdf
)


highlight_bp = Blueprint('highlight', __name__, template_folder='templates')

_EXECUTOR_FUTURES_REGISTRY = {}
REDIS_TASK_TTL = 3600  # 1 час


def _get_redis_client():
    logger = current_app.logger  # Используем логгер текущего приложения
    logger.debug(f"Attempting to get redis client. current_app object: {id(current_app)}")
    logger.debug(f"Does current_app have redis_client_tasks? {hasattr(current_app, 'redis_client_tasks')}")
    if hasattr(current_app, 'redis_client_tasks') and current_app.redis_client_tasks:
        return current_app.redis_client_tasks
    current_app.logger.warning(
        "Redis client 'redis_client_tasks' not found in current_app. Task persistence to Redis disabled.")
    return None


def _perform_highlight_processing(
        source_path: str,
        source_filename_original,
        words_path: str,
        words_filename_original,
        all_search_lines_clean: List[str],
        is_docx_source,
        perform_ocr,
        task_id,
        file_ext,
        used_predefined_list_names_for_session,
        app_config_dict
):
    logger = current_app.logger
    redis_client = _get_redis_client()

    logger.info(f"[Task {task_id}] Background processing started for '{source_filename_original or 'lists only'}'. OCR: {perform_ocr}")
    start_time_task = time.time()

    if redis_client:
        try:
            status_message = "Обработка документа..." if source_path else "Обработка списков..."
            redis_client.hmset(f"task:{task_id}", {
                "state": "PROCESSING", "status_message": status_message
            })
            redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
            
            from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
            TaskProgressRoom.send_status(task_id, "PROCESSING", status_message)
        except Exception as e_redis:
            logger.error(f"[Task {task_id}] Redis error (set PROCESSING): {e_redis}", exc_info=True)

    RESULT_DIR = app_config_dict.get('RESULT_DIR_HIGHLIGHT', app_config_dict.get('RESULT_DIR'))
    task_result_data = {
        'source_filename': source_filename_original,
        'words_filename': words_filename_original,
        'result_filename': None, 'word_stats': {}, 'phrase_stats': {}, 'total_matches': 0,
        'processing_time': 0, 'used_predefined_lists': used_predefined_list_names_for_session,
        'error': None, '_task_id_ref': task_id
    }
    output_path = None
    final_status_for_redis = 'FAILURE'

    try:
        # Если нет исходного документа, просто возвращаем информацию о списках
        if not source_path:
            logger.info(f"[Task {task_id}] No source document provided. Returning list information only.")
            # Подготавливаем данные для статистики списков (без обработки документа)
            prepared_data_unified = prepare_search_terms(all_search_lines_clean)
            # Возвращаем пустую статистику, так как документ не обрабатывался
            task_result_data['word_stats'] = {}
            task_result_data['phrase_stats'] = {}
            task_result_data['total_matches'] = 0
            final_status_for_redis = 'SUCCESS'
            logger.info(f"[Task {task_id}] List processing completed. Lists: {used_predefined_list_names_for_session}")
        else:
            # Обычная обработка с документом
            prepared_data_unified = prepare_search_terms(all_search_lines_clean)
            search_data_for_highlight = get_highlight_search_data(prepared_data_unified)
            phrase_map_for_highlight = get_highlight_phrase_map(prepared_data_unified)

            reset_caches()
            result_filename_task = f"highlighted_{task_id}{file_ext}"
            output_path = os.path.join(RESULT_DIR, result_filename_task)
            logger.info(f"[Task {task_id}] Analysis type: {file_ext}. Output: {output_path}")

            # [start] perform analyze
            # analysis_results -- структура вроде {'word_stats': {'word': {'c': 1, 'f': {'word': 1}}}, 'phrase_stats': {}, 'total_matches': 1}

            if is_docx_source:
                # prepare words for search
                analyse_data = AnalyseData()
                analyse_data.read_from_list(all_search_lines_clean)

                # search words in document
                analyser = AnalyserDocx(source_path)
                analyser.set_analyse_data(analyse_data)
                analysis_results = analyser.analyse_and_highlight(task_id=task_id)
                analyser.save(output_path)
            else:
                analysis_results = analyze_and_highlight_pdf(
                    source_path,
                    search_data_for_highlight,
                    phrase_map_for_highlight,
                    output_path,
                    use_ocr=perform_ocr
                )

            if analysis_results is None:
                task_result_data['error'] = 'Ошибка анализа документа (сервис анализа вернул None).'
                raise ValueError(task_result_data['error'])

            # [end]

            if os.path.exists(output_path) and os.path.isfile(output_path):
                task_result_data['result_filename'] = result_filename_task

            task_result_data.update(analysis_results)
            logger.info(
                f"[Task {task_id}] Analysis successful. Matches: {task_result_data.get('total_matches', 0)}. File: {result_filename_task or 'N/A'}")
            final_status_for_redis = 'SUCCESS'

    except Exception as e:
        logger.error(f"[Task {task_id}] Error during background processing: {e}", exc_info=True)
        if not task_result_data.get('error'):
            task_result_data['error'] = f'Внутренняя ошибка обработки: {str(e)}'
    finally:
        task_result_data['processing_time'] = round(time.time() - start_time_task, 2)

        if redis_client:
            try:
                status_message = "Обработка успешно завершена." if final_status_for_redis == 'SUCCESS' else task_result_data.get(
                    'error', 'Неизвестная ошибка')
                redis_payload = {
                    "state": final_status_for_redis,
                    "status_message": status_message,
                    "result_data_json": json.dumps(task_result_data)
                }
                redis_client.hmset(f"task:{task_id}", redis_payload)
                redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                
                from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
                TaskProgressRoom.send_status(task_id, final_status_for_redis, status_message)
            except Exception as e_redis:
                logger.error(f"[Task {task_id}] Redis error (final update): {e_redis}", exc_info=True)

        if source_path and os.path.exists(source_path):
            try:
                os.remove(source_path)
            except Exception as e_del:
                logger.warning(f"[Task {task_id}] Failed to delete source '{source_path}': {e_del}")
        if words_path and os.path.exists(words_path):
            try:
                os.remove(words_path)
            except Exception as e_del:
                logger.warning(f"[Task {task_id}] Failed to delete words '{words_path}': {e_del}")

        if final_status_for_redis == 'FAILURE' and output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
                task_result_data['result_filename'] = None  # Ensure result_filename is cleared
            except Exception as e_del:
                logger.warning(
                    f"[Task {task_id}] Failed to delete result file '{output_path}' after error: {e_del}")

        logger.info(
            f"[Task {task_id}] Background processing finished in {task_result_data['processing_time']} sec with state {final_status_for_redis}.")
    return task_result_data


@highlight_bp.route('/')
def index():
    session.pop('last_task_id_highlight', None)
    session.pop('last_result_data_highlight', None)
    return render_template(
        'tool_highlight/index.html',
        predefined_lists=current_app.config.get('PREDEFINED_LISTS', {}),
        analyzers_ready=current_app.config.get('ANALYZERS_READY', False)
    )


@highlight_bp.route('/process_async', methods=['POST'])
def process_async():
    start_time_request = time.time()
    logger = current_app.logger
    redis_client = _get_redis_client()
    logger.info(f"Request to /highlight/process_async. Method: {request.form.get('input-method')}")

    ANALYZERS_READY = current_app.config.get('ANALYZERS_READY', False)
    UPLOAD_DIR = current_app.config.get('UPLOAD_DIR_HIGHLIGHT', current_app.config.get('UPLOAD_DIR'))
    PREDEFINED_LISTS_DIR = current_app.config.get('PREDEFINED_LISTS_DIR')
    PREDEFINED_LISTS = current_app.config.get('PREDEFINED_LISTS', {})

    if not ANALYZERS_READY:
        return jsonify({'error': 'Сервис инициализируется, попробуйте позже.'}), 503

    task_id = str(uuid.uuid4())
    source_path, words_path = None, None
    source_filename_original, words_filename_original = None, None

    # Wrap file operations and initial Redis write in a try-finally for cleanup
    # and to ensure we can return 500 if crucial steps fail.
    try:
        # Process file uploads and prepare search terms using dedicated service
        try:
            upload_result = HighlightUploadService.process_file_upload(
                request=request,
                task_id=task_id,
                upload_dir=UPLOAD_DIR,
                predefined_lists_dir=PREDEFINED_LISTS_DIR,
                predefined_lists=PREDEFINED_LISTS
            )
            
            source_path = upload_result['source_path']
            source_filename_original = upload_result['source_filename_original']
            words_path = upload_result['words_path']
            words_filename_original = upload_result['words_filename_original']
            all_search_lines_clean = upload_result['search_terms']
            is_docx_source = upload_result['is_docx_source']
            file_ext = upload_result['file_ext']
            used_predefined_list_names_for_session = upload_result['used_predefined_list_names']
            
            # Если нет исходного документа, но есть списки, устанавливаем значения по умолчанию
            if not source_path and used_predefined_list_names_for_session:
                is_docx_source = None
                file_ext = None

        except UploadError as e:
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            logger.error(f"[Req {task_id}] Unexpected error during file upload processing: {e}", exc_info=True)
            return jsonify({'error': 'Ошибка при обработке загруженных файлов.'}), 500

        perform_ocr = request.form.get('use_ocr') == 'true'

        # --- CRITICAL: Initial Redis PENDING state write ---
        if redis_client:
            try:
                redis_client.hmset(f"task:{task_id}", {
                    "state": "PENDING", "status_message": "Задача принята в очередь",
                    "source_filename": source_filename_original or "Списки для поиска"
                })
                redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                logger.info(f"[Req {task_id}] Task state PENDING saved to Redis.")
                
                from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
                TaskProgressRoom.send_status(task_id, "PENDING", "Задача принята в очередь")
            except Exception as e_redis:
                logger.error(f"[Req {task_id}] Redis error (initial save PENDING): {e_redis}", exc_info=True)
                # Fail fast if Redis can't save initial state. Cleanup handled by outer except.
                return jsonify(
                    {'error': 'Ошибка сервера: не удалось сохранить состояние задачи. Попробуйте позже.'}), 500
        else:  # redis_client is None
            logger.error(
                f"[Req {task_id}] Redis client is not available. Cannot save task state. Task processing aborted.")
            # Cleanup handled by outer except.
            return jsonify(
                {'error': 'Ошибка конфигурации сервера: хранилище задач недоступно. Обработка невозможна.'}), 500
        # --- End CRITICAL Redis write ---

        executor = current_app.extensions.get('executor')

        if not executor:
            # This should ideally be caught at app startup, but good to have a runtime check.
            logger.critical(f"[Req {task_id}] Executor not found in current_app.extensions!")
            return jsonify({'error': 'Ошибка конфигурации сервера (Executor).'}), 500

        app_config_dict = {
            'RESULT_DIR_HIGHLIGHT': current_app.config.get('RESULT_DIR_HIGHLIGHT'),
            'RESULT_DIR': current_app.config.get('RESULT_DIR'),
        }

        future = executor.submit(
            _perform_highlight_processing,
            source_path,
            source_filename_original,
            words_path,
            words_filename_original,
            all_search_lines_clean,
            is_docx_source,
            perform_ocr,
            task_id,
            file_ext,
            used_predefined_list_names_for_session,
            app_config_dict
        )
        _EXECUTOR_FUTURES_REGISTRY[task_id] = future
        session['last_task_id_highlight'] = task_id

        # Prevent these files from being deleted by the except block if we reach here
        source_path_local, words_path_local = source_path, words_path
        source_path, words_path = None, None  # Handover to background task

        logger.info(
            f"[Req {task_id}] Task submitted. Request handling took {time.time() - start_time_request:.2f} sec.")
        return jsonify({'task_id': task_id, 'message': 'Файл принят в обработку.'}), 202

    except Exception as e:
        current_task_id_in_exc = locals().get('task_id', 'N/A_in_exception')
        logger.error(f"[Req {current_task_id_in_exc}] Error in /process_async: {e}", exc_info=True)

        # Attempt to update Redis to FAILURE if task_id was generated and Redis client available
        if redis_client and current_task_id_in_exc != 'N/A_in_exception':
            try:
                redis_client.hmset(f"task:{current_task_id_in_exc}", {
                    "state": "FAILURE", "status_message": f'Ошибка при постановке задачи: {str(e)}',
                    "result_data_json": json.dumps(
                        {'error': f'Ошибка при постановке задачи: {str(e)}', '_task_id_ref': current_task_id_in_exc})
                })
                redis_client.expire(f"task:{current_task_id_in_exc}", REDIS_TASK_TTL)
            except Exception as e_redis_fail:
                logger.error(
                    f"[Req {current_task_id_in_exc}] Redis error (update to FAILURE on initial error): {e_redis_fail}")

        return jsonify({'error': f'Внутренняя ошибка при постановке задачи: {str(e)}'}), 500
    finally:
        # Cleanup files if they weren't handed over to background task (i.e., an error occurred before handover)
        if source_path and os.path.exists(source_path):
            try:
                os.remove(source_path)
            except Exception as e_del:
                logger.warning(
                    f"[Req {locals().get('task_id', 'N/A')}] Failed to delete source '{source_path}' after error: {e_del}")
        if words_path and os.path.exists(words_path):
            try:
                os.remove(words_path)
            except Exception as e_del:
                logger.warning(
                    f"[Req {locals().get('task_id', 'N/A')}] Failed to delete words '{words_path}' after error: {e_del}")

@highlight_bp.route('/results')
def results():
    logger = current_app.logger
    task_id = request.args.get('task_id')
    
    if not task_id:
        logger.warning("Access to /results without task_id parameter. Redirecting to index.")
        return redirect(url_for('highlight.index'))
    
    from services.task.result import TaskResult
    last_result_data = TaskResult.load(task_id)
    
    if not last_result_data:
        logger.warning(f"Access to /results with task_id {task_id} but no result data found. Redirecting to index.")
        return redirect(url_for('highlight.index'))

    task_id_for_template = last_result_data.get('_task_id_ref', task_id)

    if last_result_data.get('error'):
        logger.error(
            f"Displaying results page with error for task {task_id_for_template}: {last_result_data.get('error')}")
        # --- СТАРЫЙ КОД ---
        # return render_template('tool_highlight/results.html', error=last_result_data.get('error'), task_id=task_id_for_template, **last_result_data)
        # --- НУЖНО ДОБАВИТЬ ПЕРЕДАЧУ ПУСТЫХ СПИСКОВ, ЕСЛИ ЕСТЬ ОШИБКА ---
        # Create a copy of last_result_data without 'error' to avoid duplicate argument
        template_data = {k: v for k, v in last_result_data.items() if k != 'error'}
        return render_template(
            'tool_highlight/results.html',
            error=last_result_data.get('error'),
            task_id=task_id_for_template,
            word_stats_sorted=[],  # Передаем пустые списки при ошибке
            phrase_stats_sorted=[],
            result_file_missing=False,  # Файла точно нет, если ошибка
            **template_data
        )

    RESULT_DIR = current_app.config.get('RESULT_DIR_HIGHLIGHT', current_app.config.get('RESULT_DIR'))
    result_filename = last_result_data.get('result_filename')
    result_file_missing = False  # Флаг для проверки отсутствия файла

    if result_filename:
        filepath_abs = os.path.join(RESULT_DIR, result_filename)
        # БЕЗОПАСНОСТЬ: Убедимся, что путь не выходит за пределы директории результатов
        if not os.path.normpath(filepath_abs).startswith(os.path.normpath(RESULT_DIR)):
            logger.error(f"Attempted path traversal in results check: {result_filename}")
            last_result_data['error'] = "Ошибка: Неверный путь к файлу результата."
            last_result_data['result_filename'] = None
            result_file_missing = True  # Считаем отсутствующим
            result_filename = None  # Обнуляем для дальнейшей логики
        elif not os.path.exists(filepath_abs) or not os.path.isfile(filepath_abs):
            logger.error(
                f"Result file '{result_filename}' for task {task_id_for_template} not found at '{filepath_abs}'.")
            # Обновляем сообщение об ошибке прямо в данных для передачи в шаблон
            last_result_data[
                'error'] = f"Файл результата '{result_filename}' не найден на сервере. Возможно, он был удален или произошла ошибка."
            last_result_data['result_filename'] = None  # Очищаем невалидное имя
            result_file_missing = True  # Устанавливаем флаг
    else:  # No result_filename but no error means likely no matches or dry run.
        logger.info(
            f"Displaying results for task {task_id_for_template} with no downloadable file (total_matches: {last_result_data.get('total_matches', 0)}).")

    # --- НОВЫЙ БЛОК: ИЗВЛЕЧЕНИЕ И СОРТИРОВКА СТАТИСТИКИ ---
    word_stats = last_result_data.get('word_stats', {})
    phrase_stats = last_result_data.get('phrase_stats', {})

    # Сортируем статистику для отображения в шаблоне
    # .items() возвращает пары (ключ, значение), sorted() сортирует по ключу (лемме/фразе)
    word_stats_sorted = sorted(word_stats.items()) if word_stats else []
    phrase_stats_sorted = sorted(phrase_stats.items()) if phrase_stats else []
    # ----------------------------------------------------

    # Передаем отсортированные списки и флаг отсутствия файла в шаблон
    # Исключаем ключи, которые передаются явно, чтобы избежать дублирования
    excluded_keys = {'task_id', 'word_stats_sorted', 'phrase_stats_sorted', 'result_file_missing', '_task_id_ref', 'word_stats', 'phrase_stats'}
    template_data = {k: v for k, v in last_result_data.items() if k not in excluded_keys}
    return render_template(
        'tool_highlight/results.html',
        task_id=task_id_for_template,
        word_stats_sorted=word_stats_sorted,  # <--- Передаем отсортированный список
        phrase_stats_sorted=phrase_stats_sorted,  # <--- Передаем отсортированный список
        result_file_missing=result_file_missing,  # <--- Передаем флаг
        **template_data  # Передаем остальные данные (filename, time, etc.)
    )


@highlight_bp.route('/download-result/<path:filename>')
def download_result(filename):
    logger = current_app.logger
    RESULT_DIR = current_app.config.get('RESULT_DIR_HIGHLIGHT', current_app.config.get('RESULT_DIR'))
    filepath_abs = os.path.join(RESULT_DIR, filename)

    # Security: Check for path traversal
    if not os.path.normpath(filepath_abs).startswith(os.path.normpath(RESULT_DIR)):
        logger.error(f"Attempted path traversal: {filename}")
        return "Ошибка: неверный путь к файлу.", 400

    if os.path.exists(filepath_abs) and os.path.isfile(filepath_abs):
        logger.info(f"Downloading result file: {filename}")
        return send_file(filepath_abs, as_attachment=True)
    else:
        logger.error(f"Download failed: File not found at {filepath_abs}")
        # Optionally, redirect to an error page or back to results with a message
        # For now, just return a 404 as the file is not found.
        error_msg = "Файл не найден."
        # Try to get task_id from session if possible for better context, though not directly available here.
        last_result_data = session.get('last_result_data_highlight', {})
        if last_result_data.get('result_filename') == filename:  # Check if this was the expected file
            session['last_result_data_highlight']['error'] = error_msg  # Update session error
            session['last_result_data_highlight']['result_filename'] = None
        return render_template('tool_highlight/index.html', error=error_msg), 404  # Or redirect to results


from .api.task_status import check_task_status  # noqa: F401, E402
