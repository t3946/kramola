# tool_highlight/routes.py

import os
import time
import traceback
import uuid
import json # Для сериализации/десериализации данных в Redis
from collections import Counter

try:
    import fitz # PyMuPDF
    FIT_AVAILABLE = True
except ImportError:
    FIT_AVAILABLE = False

from flask import (
    request, redirect, url_for, Blueprint, current_app, render_template,
    session, send_file, jsonify
)

from services.document_service import (
    save_uploaded_file, extract_lines_from_docx
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

try:
    from utils import load_lines_from_txt 
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    def load_lines_from_txt(filepath): 
        current_app.logger.error(f"Function 'load_lines_from_txt' could not be imported from 'utils'. Attempted to load {filepath}")
        raise FileNotFoundError(f"Utils module or function not found, cannot load {filepath}")

highlight_bp = Blueprint('highlight', __name__, template_folder='templates')

_EXECUTOR_FUTURES_REGISTRY = {}
REDIS_TASK_TTL = 3600 # 1 час

def _get_redis_client():
    logger = current_app.logger # Используем логгер текущего приложения
    logger.debug(f"Attempting to get redis client. current_app object: {id(current_app)}")
    logger.debug(f"Does current_app have redis_client_tasks? {hasattr(current_app, 'redis_client_tasks')}")
    if hasattr(current_app, 'redis_client_tasks') and current_app.redis_client_tasks:
        return current_app.redis_client_tasks
    current_app.logger.warning("Redis client 'redis_client_tasks' not found in current_app. Task persistence to Redis disabled.")
    return None

def _perform_highlight_processing(
    source_path, source_filename_original,
    words_path, words_filename_original, 
    all_search_lines_clean,
    is_docx_source, perform_ocr,
    task_id, file_ext,
    used_predefined_list_names_for_session,
    app_config_dict
    ):
    logger = current_app.logger
    redis_client = _get_redis_client()

    logger.info(f"[Task {task_id}] Background processing started for '{source_filename_original}'. OCR: {perform_ocr}")
    start_time_task = time.time()

    if redis_client:
        try:
            redis_client.hmset(f"task:{task_id}", {
                "state": "PROCESSING", "status_message": "Обработка документа..."
            })
            redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
        except Exception as e_redis: logger.error(f"[Task {task_id}] Redis error (set PROCESSING): {e_redis}", exc_info=True)

    RESULT_DIR = app_config_dict.get('RESULT_DIR_HIGHLIGHT', app_config_dict.get('RESULT_DIR'))
    task_result_data = {
        'source_filename': source_filename_original,
        'words_filename': words_filename_original, 
        'result_filename': None, 'word_stats': {}, 'phrase_stats': {}, 'total_matches': 0,
        'processing_time': 0, 'used_predefined_lists': used_predefined_list_names_for_session,
        'error': None, '_task_id_ref': task_id
    }
    result_path_task = None
    final_status_for_redis = 'FAILURE'

    try:
        if not all_search_lines_clean: 
            task_result_data['error'] = 'Список слов/фраз для поиска пуст.'
            raise ValueError(task_result_data['error'])

        logger.info(f"[Task {task_id}] Preparing {len(all_search_lines_clean)} search terms...")
        prepared_data_unified = prepare_search_terms(all_search_lines_clean)
        search_data_for_highlight = get_highlight_search_data(prepared_data_unified)
        phrase_map_for_highlight = get_highlight_phrase_map(prepared_data_unified)

        if not search_data_for_highlight.get('lemmas') and not search_data_for_highlight.get('stems') and not phrase_map_for_highlight:
            task_result_data['error'] = 'Не удалось извлечь данные для поиска из предоставленных слов/фраз.'
            raise ValueError(task_result_data['error'])

        reset_caches()
        result_filename_task = f"highlighted_{task_id}{file_ext}"
        result_path_task = os.path.join(RESULT_DIR, result_filename_task)
        logger.info(f"[Task {task_id}] Analysis type: {file_ext}. Output: {result_path_task}")

        analysis_results = None
        if is_docx_source:
            analysis_results = analyze_and_highlight_docx(source_path, search_data_for_highlight, phrase_map_for_highlight, result_path_task)
        else: 
            analysis_results = analyze_and_highlight_pdf(source_path, search_data_for_highlight, phrase_map_for_highlight, result_path_task, use_ocr=perform_ocr)

        if analysis_results is None:
            task_result_data['error'] = 'Ошибка анализа документа (сервис анализа вернул None).'
            raise ValueError(task_result_data['error'])

        if os.path.exists(result_path_task) and os.path.isfile(result_path_task):
            task_result_data['result_filename'] = result_filename_task
        
        task_result_data.update(analysis_results) 
        logger.info(f"[Task {task_id}] Analysis successful. Matches: {task_result_data.get('total_matches',0)}. File: {result_filename_task or 'N/A'}")
        final_status_for_redis = 'SUCCESS'

    except Exception as e:
        logger.error(f"[Task {task_id}] Error during background processing: {e}", exc_info=True)
        if not task_result_data.get('error'):
            task_result_data['error'] = f'Внутренняя ошибка обработки: {str(e)}'
    finally:
        task_result_data['processing_time'] = round(time.time() - start_time_task, 2)
        
        if redis_client:
            try:
                redis_payload = {
                    "state": final_status_for_redis,
                    "status_message": "Обработка успешно завершена." if final_status_for_redis == 'SUCCESS' else task_result_data.get('error', 'Неизвестная ошибка'),
                    "result_data_json": json.dumps(task_result_data)
                }
                redis_client.hmset(f"task:{task_id}", redis_payload)
                redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
            except Exception as e_redis: logger.error(f"[Task {task_id}] Redis error (final update): {e_redis}", exc_info=True)

        if source_path and os.path.exists(source_path):
            try: os.remove(source_path)
            except Exception as e_del: logger.warning(f"[Task {task_id}] Failed to delete source '{source_path}': {e_del}")
        if words_path and os.path.exists(words_path): 
            try: os.remove(words_path)
            except Exception as e_del: logger.warning(f"[Task {task_id}] Failed to delete words '{words_path}': {e_del}")
        
        if final_status_for_redis == 'FAILURE' and result_path_task and os.path.exists(result_path_task):
            try:
                os.remove(result_path_task)
                task_result_data['result_filename'] = None # Ensure result_filename is cleared
            except Exception as e_del: logger.warning(f"[Task {task_id}] Failed to delete result file '{result_path_task}' after error: {e_del}")
        
        logger.info(f"[Task {task_id}] Background processing finished in {task_result_data['processing_time']} sec with state {final_status_for_redis}.")
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
        if 'source_file' not in request.files or not request.files['source_file'].filename:
            return jsonify({'error': 'Загрузите исходный документ (.docx или .pdf)'}), 400
        
        source_file = request.files['source_file']
        source_filename_original = source_file.filename
        source_filename_lower = source_filename_original.lower()
        is_docx_source = source_filename_lower.endswith('.docx')
        is_pdf_source = source_filename_lower.endswith('.pdf')

        if not is_docx_source and not is_pdf_source:
            return jsonify({'error': 'Недопустимый формат исходного файла. Загрузите .docx или .pdf'}), 400
        if is_pdf_source and not FIT_AVAILABLE:
             return jsonify({'error': 'Обработка PDF файлов недоступна на сервере (PyMuPDF).'}), 400

        file_ext = ".docx" if is_docx_source else ".pdf"
        source_filename_unique = f"source_{task_id}{file_ext}"
        source_path = save_uploaded_file(source_file, UPLOAD_DIR, source_filename_unique)
        if not source_path: # Should already be caught by save_uploaded_file's potential exceptions
            return jsonify({'error': 'Ошибка при сохранении исходного документа.'}), 500
        logger.info(f"[Req {task_id}] Source file '{source_filename_original}' saved as '{source_filename_unique}'")
        
        search_lines_from_file = []
        words_file_input = request.files.get('words_file')
        if words_file_input and words_file_input.filename:
            words_filename_original = words_file_input.filename
            words_filename_lower = words_filename_original.lower()
            logger.info(f"[Req {task_id}] Received words_file: '{words_filename_original}'")

            if not (words_filename_lower.endswith('.docx') or words_filename_lower.endswith('.xlsx')):
                 return jsonify({'error': 'Файл слов должен быть в формате .docx или .xlsx'}), 400 # Cleanup handled by outer try-except
            
            if words_filename_lower.endswith('.docx'):
                words_filename_unique = f"words_{task_id}.docx"
                words_path = save_uploaded_file(words_file_input, UPLOAD_DIR, words_filename_unique)
                if not words_path:
                    return jsonify({'error': 'Ошибка сохранения файла слов (.docx).'}), 500
                logger.info(f"[Req {task_id}] Words file (.docx) saved as '{words_filename_unique}'")
                try:
                    search_lines_from_file = extract_lines_from_docx(words_path)
                    if not isinstance(search_lines_from_file, list): search_lines_from_file = []
                    logger.info(f"[Req {task_id}] Extracted {len(search_lines_from_file)} lines from '{words_filename_original}'")
                except Exception as e:
                    logger.error(f"[Req {task_id}] Error reading DOCX words file '{words_path}': {e}", exc_info=True)
                    search_lines_from_file = [] # Or return error
            elif words_filename_lower.endswith('.xlsx'):
                logger.warning(f"[Req {task_id}] XLSX words file '{words_filename_original}' received. Backend will treat as empty unless explicit XLSX parsing is added.")
                # words_path is not set for xlsx currently, so it won't be auto-deleted unless saved.
                search_lines_from_file = []

        search_lines_from_text = []
        words_text_raw = request.form.get('words_text', '')
        if words_text_raw.strip():
            lines_from_text = words_text_raw.replace(',', '\n').splitlines()
            search_lines_from_text = [line.strip() for line in lines_from_text if line.strip()]
            logger.info(f"[Req {task_id}] Received {len(search_lines_from_text)} lines from textarea.")

        additional_search_lines = []
        used_predefined_list_names_for_session = []
        selected_list_keys = request.form.getlist('predefined_list_keys')
        if selected_list_keys:
            logger.info(f"[Req {task_id}] Selected predefined lists: {selected_list_keys}")
            for key in selected_list_keys:
                if not key or key not in PREDEFINED_LISTS:
                    logger.warning(f"[Req {task_id}] Invalid or unknown predefined list key: '{key}'")
                    continue
                filepath = os.path.join(PREDEFINED_LISTS_DIR, f"{key}.txt")
                display_name = PREDEFINED_LISTS[key]
                try:
                    lines = load_lines_from_txt(filepath)
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    if cleaned_lines:
                        additional_search_lines.extend(cleaned_lines)
                        used_predefined_list_names_for_session.append(display_name)
                        logger.info(f"[Req {task_id}] Loaded {len(cleaned_lines)} lines from predefined list '{display_name}' ({key}.txt)")
                except FileNotFoundError:
                    logger.error(f"[Req {task_id}] Predefined list file not found: {filepath}")
                except Exception as e:
                    logger.error(f"[Req {task_id}] Error loading predefined list '{display_name}' ({key}.txt): {e}", exc_info=True)

        all_search_lines = search_lines_from_file + search_lines_from_text + additional_search_lines
        logger.info(f"[Req {task_id}] Total lines before cleaning: {len(all_search_lines)}. From file: {len(search_lines_from_file)}, text: {len(search_lines_from_text)}, predefined: {len(additional_search_lines)}")
        
        if not all_search_lines:
             logger.error(f"[Req {task_id}] No word source provided (file, text, or predefined).")
             return jsonify({'error': 'Укажите источник слов: файл, текстовое поле или выберите список.'}), 400

        unique_lines_dict = {line.strip().lower(): line.strip() for line in all_search_lines if line.strip()}
        all_search_lines_clean = list(unique_lines_dict.values())
        if not all_search_lines_clean:
             logger.error(f"[Req {task_id}] All search lines are empty after cleaning.")
             return jsonify({'error': 'Предоставленные слова/фразы пусты или некорректны.'}), 400
        logger.info(f"[Req {task_id}] Total unique non-empty search lines: {len(all_search_lines_clean)}")
        
        perform_ocr = request.form.get('use_ocr') == 'true'

        # --- CRITICAL: Initial Redis PENDING state write ---
        if redis_client:
            try:
                redis_client.hmset(f"task:{task_id}", {
                    "state": "PENDING", "status_message": "Задача принята в очередь",
                    "source_filename": source_filename_original
                })
                redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                logger.info(f"[Req {task_id}] Task state PENDING saved to Redis.")
            except Exception as e_redis:
                logger.error(f"[Req {task_id}] Redis error (initial save PENDING): {e_redis}", exc_info=True)
                # Fail fast if Redis can't save initial state. Cleanup handled by outer except.
                return jsonify({'error': 'Ошибка сервера: не удалось сохранить состояние задачи. Попробуйте позже.'}), 500
        else: # redis_client is None
            logger.error(f"[Req {task_id}] Redis client is not available. Cannot save task state. Task processing aborted.")
            # Cleanup handled by outer except.
            return jsonify({'error': 'Ошибка конфигурации сервера: хранилище задач недоступно. Обработка невозможна.'}), 500
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
            source_path, source_filename_original,
            words_path, words_filename_original, 
            all_search_lines_clean,
            is_docx_source, perform_ocr,
            task_id, file_ext,
            used_predefined_list_names_for_session,
            app_config_dict
        )
        _EXECUTOR_FUTURES_REGISTRY[task_id] = future
        session['last_task_id_highlight'] = task_id
        
        # Prevent these files from being deleted by the except block if we reach here
        source_path_local, words_path_local = source_path, words_path 
        source_path, words_path = None, None # Handover to background task

        logger.info(f"[Req {task_id}] Task submitted. Request handling took {time.time() - start_time_request:.2f} sec.")
        return jsonify({'task_id': task_id, 'message': 'Файл принят в обработку.'}), 202

    except Exception as e: 
        current_task_id_in_exc = locals().get('task_id', 'N/A_in_exception')
        logger.error(f"[Req {current_task_id_in_exc}] Error in /process_async: {e}", exc_info=True)
        
        # Attempt to update Redis to FAILURE if task_id was generated and Redis client available
        if redis_client and current_task_id_in_exc != 'N/A_in_exception':
            try:
                redis_client.hmset(f"task:{current_task_id_in_exc}", {
                    "state": "FAILURE", "status_message": f'Ошибка при постановке задачи: {str(e)}',
                    "result_data_json": json.dumps({'error': f'Ошибка при постановке задачи: {str(e)}', '_task_id_ref': current_task_id_in_exc})
                })
                redis_client.expire(f"task:{current_task_id_in_exc}", REDIS_TASK_TTL)
            except Exception as e_redis_fail: logger.error(f"[Req {current_task_id_in_exc}] Redis error (update to FAILURE on initial error): {e_redis_fail}")
        
        return jsonify({'error': f'Внутренняя ошибка при постановке задачи: {str(e)}'}), 500
    finally:
        # Cleanup files if they weren't handed over to background task (i.e., an error occurred before handover)
        if source_path and os.path.exists(source_path):
            try: os.remove(source_path)
            except Exception as e_del: logger.warning(f"[Req {locals().get('task_id', 'N/A')}] Failed to delete source '{source_path}' after error: {e_del}")
        if words_path and os.path.exists(words_path): 
            try: os.remove(words_path)
            except Exception as e_del: logger.warning(f"[Req {locals().get('task_id', 'N/A')}] Failed to delete words '{words_path}' after error: {e_del}")


@highlight_bp.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    logger = current_app.logger
    redis_client = _get_redis_client()

    task_info_from_redis_initial = None
    if redis_client:
        try:
            raw_redis_data = redis_client.hgetall(f"task:{task_id}")
            if raw_redis_data:
                task_info_from_redis_initial = {k: v for k, v in raw_redis_data.items()} # Ensure mutable copy
        except Exception as e_redis_get:
            logger.error(f"Task {task_id}: Redis error getting initial task status: {e_redis_get}", exc_info=True)
            # Continue, will rely on future or ultimately fail if Redis is persistently down

    active_future = _EXECUTOR_FUTURES_REGISTRY.get(task_id)

    if active_future:
        if active_future.running():
            if redis_client and task_info_from_redis_initial and task_info_from_redis_initial.get('state') == 'PENDING':
                try:
                    redis_client.hmset(f"task:{task_id}", {"state": "PROCESSING", "status_message": "Задача выполняется..."})
                    redis_client.expire(f"task:{task_id}", REDIS_TASK_TTL)
                except Exception as e_redis_run: logger.error(f"Task {task_id}: Redis error updating to PROCESSING: {e_redis_run}")
            elif redis_client and not task_info_from_redis_initial: # Future running but no Redis record yet
                 logger.warning(f"Task {task_id} running, but no initial Redis record. Background task should create it.")
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
                        _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None) # Clean up
                        return jsonify({'state': state, 'status': status_msg, 'result_data_for_session': True})
                    except json.JSONDecodeError:
                        logger.error(f"Task {task_id}: Could not decode result_data_json from Redis: {raw_redis_data_final['result_data_json']}")
                        # Fall through to future.result()
                else:
                    logger.warning(f"Task {task_id}: Future done, but no final/complete record in Redis. Will try future.result().")

            # If not successfully retrieved from Redis (or Redis client is None)
            logger.warning(f"Task {task_id}: Attempting to get result from future.result() as Redis fallback.")
            try:
                # The 'active_future' variable holds the future object.
                result_from_future = active_future.result() 
                session['last_result_data_highlight'] = result_from_future
                is_error = bool(result_from_future.get('error'))
                final_status_msg = result_from_future.get('error') or 'Задача завершена (результат из future).'
                logger.info(f"Task {task_id} obtained result directly from future. Error: {is_error}")
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None) # Clean up
                return jsonify({
                    'state': 'FAILURE' if is_error else 'SUCCESS',
                    'status': final_status_msg,
                    'result_data_for_session': True
                })
            except Exception as e_future_res_direct:
                logger.error(f"Task {task_id} critical error: future.result() failed: {e_future_res_direct}", exc_info=True)
                critical_error_msg = 'Критическая ошибка: результат задачи не может быть получен.'
                session['last_result_data_highlight'] = {'error': critical_error_msg, '_task_id_ref': task_id}
                _EXECUTOR_FUTURES_REGISTRY.pop(task_id, None) # Clean up
                return jsonify({'state': 'FAILURE', 'status': critical_error_msg, 'result_data_for_session': True})

    # If future is not in registry (e.g., already processed and popped, or app restarted)
    # Rely solely on Redis if available and had initial info.
    if task_info_from_redis_initial: # From the very first Redis check
        state = task_info_from_redis_initial.get("state", "UNKNOWN")
        status_msg = task_info_from_redis_initial.get("status_message", "Статус из Redis")
        # If result_data_json is present, it means task completed and Redis has it.
        if 'result_data_json' in task_info_from_redis_initial:
            try:
                session['last_result_data_highlight'] = json.loads(task_info_from_redis_initial['result_data_json'])
                return jsonify({'state': state, 'status': status_msg, 'result_data_for_session': (state in ["SUCCESS", "FAILURE"])})
            except json.JSONDecodeError:
                 logger.error(f"Task {task_id}: Could not decode result_data_json from task_info_from_redis_initial.")
                 # Fall through to NOT_FOUND or treat as error
        else: # No final result in Redis, but an initial record existed (e.g. PENDING, PROCESSING)
            logger.warning(f"Task {task_id} not in active futures. Initial Redis state was '{state}'. Final result missing.")
            # This could mean the task is still genuinely processing by a worker, but this status check lost track of the live future.
            # Or it failed and Redis didn't get updated.
            # Returning current (possibly non-final) state. Client will continue polling.
            return jsonify({'state': state, 'status': status_msg, 'result_data_for_session': False}) 
            
    logger.warning(f"Task {task_id} not found in active futures or Redis (final check).")
    return jsonify({'state': 'NOT_FOUND', 'status': 'Задача не найдена или информация о ней утеряна.'}), 404


@highlight_bp.route('/results')
def results():
    logger = current_app.logger
    last_result_data = session.get('last_result_data_highlight')

    if not last_result_data:
        logger.warning("Access to /results without last_result_data_highlight in session. Redirecting to index.")
        return redirect(url_for('highlight.index'))

    # Ensure task_id is available for template, even if it's from _task_id_ref
    task_id_for_template = last_result_data.get('_task_id_ref', 'N/A')

    if last_result_data.get('error'):
        logger.error(f"Displaying results page with error for task {task_id_for_template}: {last_result_data.get('error')}")
        # --- СТАРЫЙ КОД ---
        # return render_template('tool_highlight/results.html', error=last_result_data.get('error'), task_id=task_id_for_template, **last_result_data)
        # --- НУЖНО ДОБАВИТЬ ПЕРЕДАЧУ ПУСТЫХ СПИСКОВ, ЕСЛИ ЕСТЬ ОШИБКА ---
        return render_template(
            'tool_highlight/results.html',
            error=last_result_data.get('error'),
            task_id=task_id_for_template,
            word_stats_sorted=[], # Передаем пустые списки при ошибке
            phrase_stats_sorted=[],
            result_file_missing=False, # Файла точно нет, если ошибка
            **last_result_data
        )


    RESULT_DIR = current_app.config.get('RESULT_DIR_HIGHLIGHT', current_app.config.get('RESULT_DIR'))
    result_filename = last_result_data.get('result_filename')
    result_file_missing = False # Флаг для проверки отсутствия файла

    if result_filename:
        filepath_abs = os.path.join(RESULT_DIR, result_filename)
        # БЕЗОПАСНОСТЬ: Убедимся, что путь не выходит за пределы директории результатов
        if not os.path.normpath(filepath_abs).startswith(os.path.normpath(RESULT_DIR)):
             logger.error(f"Attempted path traversal in results check: {result_filename}")
             last_result_data['error'] = "Ошибка: Неверный путь к файлу результата."
             last_result_data['result_filename'] = None
             result_file_missing = True # Считаем отсутствующим
             result_filename = None # Обнуляем для дальнейшей логики
        elif not os.path.exists(filepath_abs) or not os.path.isfile(filepath_abs):
            logger.error(f"Result file '{result_filename}' for task {task_id_for_template} not found at '{filepath_abs}'.")
            # Обновляем сообщение об ошибке прямо в данных для передачи в шаблон
            last_result_data['error'] = f"Файл результата '{result_filename}' не найден на сервере. Возможно, он был удален или произошла ошибка."
            last_result_data['result_filename'] = None # Очищаем невалидное имя
            result_file_missing = True # Устанавливаем флаг
    else: # No result_filename but no error means likely no matches or dry run.
        logger.info(f"Displaying results for task {task_id_for_template} with no downloadable file (total_matches: {last_result_data.get('total_matches', 0)}).")

    # --- НОВЫЙ БЛОК: ИЗВЛЕЧЕНИЕ И СОРТИРОВКА СТАТИСТИКИ ---
    word_stats = last_result_data.get('word_stats', {})
    phrase_stats = last_result_data.get('phrase_stats', {})

    # Сортируем статистику для отображения в шаблоне
    # .items() возвращает пары (ключ, значение), sorted() сортирует по ключу (лемме/фразе)
    word_stats_sorted = sorted(word_stats.items()) if word_stats else []
    phrase_stats_sorted = sorted(phrase_stats.items()) if phrase_stats else []
    # ----------------------------------------------------

    # Передаем отсортированные списки и флаг отсутствия файла в шаблон
    return render_template(
        'tool_highlight/results.html',
        task_id=task_id_for_template,
        word_stats_sorted=word_stats_sorted,   # <--- Передаем отсортированный список
        phrase_stats_sorted=phrase_stats_sorted, # <--- Передаем отсортированный список
        result_file_missing=result_file_missing, # <--- Передаем флаг
        **last_result_data                      # Передаем остальные данные (filename, time, etc.)
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
        if last_result_data.get('result_filename') == filename: # Check if this was the expected file
             session['last_result_data_highlight']['error'] = error_msg # Update session error
             session['last_result_data_highlight']['result_filename'] = None
        return render_template('tool_highlight/index.html', error=error_msg), 404 # Or redirect to results