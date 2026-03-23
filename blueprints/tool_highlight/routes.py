import os
import shutil
import time
import uuid
import json
from datetime import datetime, timezone
from typing import List

from utils.decorators import require_query_params

from application.controllers import ResultsController, InagentDetailsController
from services.analysis import AnalysisData, AnalyserDocx
from services.task import TaskStatus
from services.task.redis_fields import (
    REDIS_TASK_CREATED_AT,
    REDIS_TASK_SOURCE_ARCHIVED_FILENAME,
    REDIS_TASK_SOURCE_FILENAME,
    REDIS_TASK_SOURCE_FILE_EXT,
)
from services.task.result import TaskResult


from flask import (
    request, redirect, url_for, Blueprint, current_app, render_template,
    session, send_file, jsonify, flash, get_flashed_messages
)

from services.highlight_upload import (
    HighlightUploadService, UploadError
)
from services.pymorphy_service import (
    reset_caches
)
from services.analysis.analyser_pdf import AnalyserPdf

from services.words_list import ListFromText, ListFromTextExclude


highlight_bp = Blueprint('highlight', __name__, template_folder='templates')

_EXECUTOR_FUTURES_REGISTRY = {}


def _get_redis_client():
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
        selected_list_keys: List[str],
        is_docx_source,
        perform_ocr,
        task_id,
        file_ext,
        used_predefined_list_names_for_session,
        app_config_dict,
        task_created_at_iso: str,
        exclude_path: str = None
):
    logger = current_app.logger
    redis_client = _get_redis_client()
    start_time_task = time.time()

    if redis_client:
        try:
            status_message = "Обработка документа..."
            redis_client.hmset(f"task:{task_id}", {
                "state": TaskStatus.PROCESSING.value, "status_message": status_message
            })
            redis_client.expire(f"task:{task_id}", current_app.config["REDIS_TASK_TTL"])

            from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
            TaskProgressRoom.send_status(task_id, TaskStatus.PROCESSING.value, status_message)
        except Exception as e_redis:
            logger.error(f"[Task {task_id}] Redis error (set PROCESSING): {e_redis}", exc_info=True)

    RESULT_DIR = app_config_dict.get('RESULT_DIR_HIGHLIGHT', app_config_dict.get('RESULT_DIR'))
    task_result_data = {
        'source_filename': source_filename_original,
        'words_filename': words_filename_original,
        'result_filename': None, 'stats': [], 'total_matches': 0,
        'processing_time': 0, 'used_predefined_lists': used_predefined_list_names_for_session,
        'error': None, '_task_id_ref': task_id,
        'created_at': task_created_at_iso,
    }
    output_path = None
    final_status_for_redis = TaskStatus.COMPLETED

    try:
        reset_caches()
        result_filename_task = f"highlighted_{task_id}{file_ext}"
        output_path = os.path.join(RESULT_DIR, result_filename_task)

        # [start] perform analyze
        # analysis_results -- структура вроде {'word_stats': {'word': {'c': 1, 'f': {'word': 1}}}, 'phrase_stats': {}, 'total_matches': 1}

        analyse_data = AnalysisData()
        analyse_data.load_user_list(task_id=task_id)

        if selected_list_keys:
            analyse_data.load_predefined_lists(selected_list_keys)

        analyse_data.apply_exclude_user_list(task_id)

        if is_docx_source:
            analyser = AnalyserDocx(source_path)
            analyser.set_analyse_data(analyse_data)
            analysis_results = analyser.analyse_and_highlight(task_id=task_id)
            analyser.save(output_path)
        else:
            analyser = AnalyserPdf(source_path)
            analyser.set_analyse_data(analyse_data)
            analysis_results = analyser.analyse_and_highlight(task_id=task_id, use_ocr=perform_ocr)
            analyser.save(output_path)

        if analysis_results is None:
            task_result_data['error'] = 'Ошибка анализа документа (сервис анализа вернул None).'
            raise ValueError(task_result_data['error'])

        # [end]

        if os.path.exists(output_path) and os.path.isfile(output_path):
            task_result_data['result_filename'] = result_filename_task

        task_result_data.update(analysis_results)
        final_status_for_redis = TaskStatus.COMPLETED

    except Exception as e:
        logger.error(f"[Task {task_id}] Error during background processing: {e}", exc_info=True)
        if not task_result_data.get('error'):
            task_result_data['error'] = f'Внутренняя ошибка обработки: {str(e)}'
    finally:
        task_result_data['processing_time'] = round(time.time() - start_time_task, 2)

        source_archived_filename: str | None = None

        if RESULT_DIR and source_path and os.path.isfile(source_path):
            archive_name: str = f"source_{task_id}{file_ext}"
            archive_path: str = os.path.join(RESULT_DIR, archive_name)

            try:
                shutil.copy2(source_path, archive_path)
                source_archived_filename = archive_name
            except OSError as e_copy:
                logger.warning(f"[Task {task_id}] Failed to archive source to '{archive_path}': {e_copy}")

        if redis_client:
            try:
                status_message = "Обработка успешно завершена." if not task_result_data.get('error') else task_result_data.get(
                    'error', 'Неизвестная ошибка')
                redis_payload = {
                    "state": final_status_for_redis.value,
                    "status_message": status_message,
                    "result_data_json": json.dumps(task_result_data),
                    REDIS_TASK_CREATED_AT: task_created_at_iso,
                }

                if source_archived_filename:
                    redis_payload[REDIS_TASK_SOURCE_ARCHIVED_FILENAME] = source_archived_filename

                redis_client.hmset(f"task:{task_id}", redis_payload)
                redis_client.expire(f"task:{task_id}", current_app.config["REDIS_TASK_TTL"])

                from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
                TaskProgressRoom.send_status(task_id, final_status_for_redis.value, status_message)
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

        if exclude_path and os.path.exists(exclude_path):
            try:
                os.remove(exclude_path)
            except Exception as e_del:
                logger.warning(f"[Task {task_id}] Failed to delete exclude '{exclude_path}': {e_del}")

        if task_result_data.get('error') and output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
                task_result_data['result_filename'] = None  # Ensure result_filename is cleared
            except Exception as e_del:
                logger.warning(
                    f"[Task {task_id}] Failed to delete result file '{output_path}' after error: {e_del}")

    return task_result_data


@highlight_bp.route('/')
def index():
    session.pop('last_task_id_highlight', None)
    session.pop('last_result_data_highlight', None)
    messages = get_flashed_messages()
    error = messages[0] if messages else None
    return render_template(
        'tool_highlight/index.html',
        predefined_lists=current_app.config.get('PREDEFINED_LISTS', {}),
        analyzers_ready=current_app.config.get('ANALYZERS_READY', False),
        error=error
    )


@highlight_bp.route('/process_async', methods=['POST'])
def process_async():
    start_time_request = time.time()
    logger = current_app.logger
    redis_client = _get_redis_client()

    ANALYZERS_READY = current_app.config.get('ANALYZERS_READY', False)
    UPLOAD_DIR = current_app.config.get('UPLOAD_DIR_HIGHLIGHT', current_app.config.get('UPLOAD_DIR'))
    PREDEFINED_LISTS_DIR = current_app.config.get('PREDEFINED_LISTS_DIR')
    PREDEFINED_LISTS = current_app.config.get('PREDEFINED_LISTS', {})

    if not ANALYZERS_READY:
        return jsonify({'error': 'Сервис инициализируется, попробуйте позже.'}), 503

    task_id = str(uuid.uuid4())
    task_created_at_iso: str | None = None
    source_path, words_path = None, None
    source_filename_original, words_filename_original = None, None
    exclude_path = None

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
            user_search_terms = upload_result.get('user_search_terms', [])
            is_docx_source = upload_result['is_docx_source']
            file_ext = upload_result['file_ext']
            used_predefined_list_names_for_session = upload_result['used_predefined_list_names']
            selected_list_keys = upload_result.get('selected_list_keys', [])
            exclude_path = upload_result.get('exclude_path')
            exclude_lines = upload_result.get('exclude_lines', [])

            if not source_path:
                return jsonify({'error': 'Исходный документ обязателен.'}), 400

        except UploadError as e:
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            logger.error(f"[Req {task_id}] Unexpected error during file upload processing: {e}", exc_info=True)
            return jsonify({'error': 'Ошибка при обработке загруженных файлов.'}), 500

        perform_ocr = request.form.get('use_ocr') == 'true'
        task_created_at_iso = datetime.now(timezone.utc).isoformat()

        # --- CRITICAL: Initial Redis PENDING state write ---
        if redis_client:
            try:
                redis_client.hmset(f"task:{task_id}", {
                    "state": TaskStatus.PENDING.value,
                    "status_message": "Задача принята в очередь",
                    REDIS_TASK_SOURCE_FILENAME: source_filename_original or "Документ",
                    REDIS_TASK_SOURCE_FILE_EXT: file_ext,
                    REDIS_TASK_CREATED_AT: task_created_at_iso,
                })
                redis_client.expire(f"task:{task_id}", current_app.config["REDIS_TASK_TTL"])

                # [start] save user lists to Redis: from file if uploaded, else from text
                if words_path:
                    ListFromText(task_id).save_from_file(words_path)
                elif len(user_search_terms) > 0:
                    ListFromText(task_id).save_from_text(user_search_terms)

                if exclude_path:
                    ListFromTextExclude(task_id).save_from_file(exclude_path)
                elif exclude_lines:
                    ListFromTextExclude(task_id).save_from_text(exclude_lines)
                # [end]

                from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom
                TaskProgressRoom.send_status(task_id, TaskStatus.PENDING.value, "Задача принята в очередь")
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
            selected_list_keys,
            is_docx_source,
            perform_ocr,
            task_id,
            file_ext,
            used_predefined_list_names_for_session,
            app_config_dict,
            task_created_at_iso,
            exclude_path
        )
        _EXECUTOR_FUTURES_REGISTRY[task_id] = future
        session['last_task_id_highlight'] = task_id

        # Prevent these files from being deleted by the except block if we reach here
        source_path_local, words_path_local, exclude_path_local = source_path, words_path, exclude_path
        source_path, words_path, exclude_path = None, None, None  # Handover to background task

        return jsonify({'task_id': task_id, 'message': 'Файл принят в обработку.'}), 202

    except Exception as e:
        current_task_id_in_exc = locals().get('task_id', 'N/A_in_exception')
        logger.error(f"[Req {current_task_id_in_exc}] Error in /process_async: {e}", exc_info=True)

        # Attempt to update Redis to COMPLETED if task_id was generated and Redis client available
        if redis_client and current_task_id_in_exc != 'N/A_in_exception':
            try:
                created_at_on_error: str = (
                    task_created_at_iso
                    if task_created_at_iso
                    else datetime.now(timezone.utc).isoformat()
                )
                redis_client.hmset(f"task:{current_task_id_in_exc}", {
                    "state": TaskStatus.COMPLETED.value,
                    "status_message": f'Ошибка при постановке задачи: {str(e)}',
                    "result_data_json": json.dumps({
                        'error': f'Ошибка при постановке задачи: {str(e)}',
                        '_task_id_ref': current_task_id_in_exc,
                        'created_at': created_at_on_error,
                    }),
                    REDIS_TASK_CREATED_AT: created_at_on_error,
                })
                redis_client.expire(f"task:{current_task_id_in_exc}", current_app.config["REDIS_TASK_TTL"])
            except Exception as e_redis_fail:
                logger.error(
                    f"[Req {current_task_id_in_exc}] Redis error (update to COMPLETED on initial error): {e_redis_fail}")

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
        if exclude_path and os.path.exists(exclude_path):
            try:
                os.remove(exclude_path)
            except Exception as e_del:
                logger.warning(
                    f"[Req {locals().get('task_id', 'N/A')}] Failed to delete exclude '{exclude_path}' after error: {e_del}")

@highlight_bp.route('/results')
@require_query_params('task_id', redirect_endpoint='highlight.index')
def results():
    task_id = request.args.get('task_id')
    last_result_data = TaskResult.load(task_id)

    if not last_result_data:
        return redirect(url_for('highlight.index'))

    if last_result_data.get('error'):
        flash(last_result_data.get('error'))
        return redirect(url_for('highlight.index'))

    return ResultsController.render(task_id)


@highlight_bp.route('/inagent-details')
def inagent_details_fragment():
    phrase = request.args.get("phrase", "").strip()
    return InagentDetailsController.render_fragment(phrase)


@highlight_bp.route('/download-source/<task_id>')
def download_source(task_id: str):
    logger = current_app.logger
    redis_client = _get_redis_client()

    if not redis_client:
        return "Хранилище задач недоступно.", 503

    raw_fields = redis_client.hgetall(f"task:{task_id}")

    if not raw_fields:
        return "Задача не найдена.", 404

    fields: dict[str, str] = {}

    for rk, rv in raw_fields.items():
        ks: str = rk.decode() if isinstance(rk, bytes) else rk
        vs: str = rv.decode() if isinstance(rv, bytes) else rv
        fields[ks] = vs

    archived: str | None = fields.get(REDIS_TASK_SOURCE_ARCHIVED_FILENAME)

    if not archived:
        return "Исходный файл не сохранён (задача ещё в очереди или архив недоступен).", 404

    expected_prefix: str = f"source_{task_id}"

    if ".." in archived or "/" in archived or "\\" in archived:
        logger.error(f"Invalid source archive name for task {task_id}: {archived}")
        return "Некорректное имя файла.", 400

    if not archived.startswith(expected_prefix):
        logger.error(f"Source archive name mismatch for task {task_id}: {archived}")
        return "Некорректное имя файла.", 400

    RESULT_DIR = current_app.config.get('RESULT_DIR_HIGHLIGHT', current_app.config.get('RESULT_DIR'))

    if not RESULT_DIR:
        logger.error("RESULT_DIR is not configured; cannot serve source archive.")
        return "Каталог результатов не настроен.", 500

    filepath_abs: str = os.path.join(RESULT_DIR, archived)

    if not os.path.normpath(filepath_abs).startswith(os.path.normpath(RESULT_DIR)):
        return "Ошибка: неверный путь к файлу.", 400

    if os.path.exists(filepath_abs) and os.path.isfile(filepath_abs):
        return send_file(
            filepath_abs,
            as_attachment=True,
            download_name=fields.get(REDIS_TASK_SOURCE_FILENAME) or archived,
        )

    logger.error(f"Source archive missing on disk: {filepath_abs}")
    return "Файл источника не найден на сервере.", 404


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
