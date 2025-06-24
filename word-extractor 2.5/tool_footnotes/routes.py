# --- START OF FILE routes.py --- (tool_footnotes/routes.py) - ADAPTED FOR UNIFIED PYMORPHY

import os
import time
import traceback
import json
from flask import (
    request, redirect, url_for, Blueprint, current_app, render_template,
    session, send_file
)

# Сервисы
from services.document_service import (
    save_uploaded_file, extract_lines_from_docx, TOKEN_PATTERN
)
# --- ИЗМЕНЕННЫЕ ИМПОРТЫ из pymorphy_service ---
from services.pymorphy_service import (
    get_morph_analyzer, # Оставляем, если нужен для проверок
    prepare_search_terms, # <--- НОВАЯ функция подготовки
    get_footnotes_word_maps, # <--- НОВЫЙ адаптер
    get_footnotes_phrase_maps, # <--- НОВЫЙ адаптер
    reset_caches # <--- НОВЫЙ сброс кэша (если нужен)
    # get_search_maps_data, # <--- Удалено
    # get_search_phrase_maps_data # <--- Удалено
)
# Импортируем сервис обработки (без изменений)
from services.footnotes_service import analyze_and_highlight_terms_docx as analyze_and_process_docx

# Регистрация блюпринта
footnotes_bp = Blueprint('footnotes', __name__, template_folder='templates')

# --- Константы ---
STATS_FILE_SUFFIX = "_stats.json"

@footnotes_bp.route('/')
def index():
    """Отображает главную страницу инструмента."""
    session.pop('last_result_data_footnotes', None)
    # current_app.logger.info("Запрос /footnotes/, сессия очищена.") # Логгер может быть недоступен, если удален из Flask app
    analyzers_ready = current_app.config.get('ANALYZERS_READY', False)
    return render_template(
        'tool_footnotes/index.html',
        analyzers_ready=analyzers_ready
    )

@footnotes_bp.route('/process', methods=['POST'])
def process():
    """
    Обрабатывает файлы, ищет слова/фразы по ЛЕММАМ или СТЕММАМ, добавляет подсветку.
    Использует унифицированную подготовку данных.
    """
    start_time = time.time()
    # current_app.logger.info("Начало обработки запроса /footnotes/process (унифицированная подготовка)")

    # --- Конфигурация ---
    ANALYZERS_READY = current_app.config.get('ANALYZERS_READY', False)
    UPLOAD_DIR = current_app.config.get('UPLOAD_DIR_FOOTNOTES', current_app.config.get('UPLOAD_DIR'))
    RESULT_DIR = current_app.config.get('RESULT_DIR_FOOTNOTES', current_app.config.get('RESULT_DIR'))

    if not ANALYZERS_READY:
        # current_app.logger.error(...)
        return render_template('tool_footnotes/index.html',
                               error='Ошибка сервера: Морфологические анализаторы не загружены.',
                               analyzers_ready=ANALYZERS_READY)

    # Можно оставить проверку Pymorphy, если он критичен для работы footnotes_service
    morph = get_morph_analyzer()
    if not morph:
         pass # current_app.logger.warning(...)

    timestamp_str = str(int(start_time))
    source_path = None; words_path = None; stats_file_path = None

    try:
        # 1. Получение исходного файла (.docx) - без изменений
        if 'source_file' not in request.files or not request.files['source_file'].filename:
            return render_template('tool_footnotes/index.html', error='Необходимо загрузить исходный документ (.docx)', analyzers_ready=ANALYZERS_READY)
        source_file = request.files['source_file']
        if not source_file.filename.lower().endswith('.docx'):
            return render_template('tool_footnotes/index.html', error='Исходный документ должен быть в формате .docx', analyzers_ready=ANALYZERS_READY)
        source_path = save_uploaded_file(source_file, UPLOAD_DIR, f"source_footnotes_{timestamp_str}.docx")

        # 2. Получение файла слов/фраз (.docx) - без изменений
        if 'words_file' not in request.files or not request.files['words_file'].filename:
             if source_path and os.path.exists(source_path): os.remove(source_path)
             return render_template('tool_footnotes/index.html', error='Необходимо загрузить файл со словами/фразами для поиска (.docx)', analyzers_ready=ANALYZERS_READY)
        words_file = request.files['words_file']
        if not words_file.filename.lower().endswith('.docx'):
             if source_path and os.path.exists(source_path): os.remove(source_path)
             return render_template('tool_footnotes/index.html', error='Файл со словами/фразами для поиска должен быть в формате .docx', analyzers_ready=ANALYZERS_READY)
        words_path = save_uploaded_file(words_file, UPLOAD_DIR, f"words_footnotes_{timestamp_str}.docx")
        words_filename_for_session = words_file.filename
        try:
             search_lines_from_docx = extract_lines_from_docx(words_path)

        except Exception as e_extract:

              if source_path and os.path.exists(source_path): os.remove(source_path)
              if words_path and os.path.exists(words_path): os.remove(words_path)
              return render_template('tool_footnotes/index.html', error=f'Ошибка чтения файла слов/фраз ({words_file.filename}).', analyzers_ready=ANALYZERS_READY)

        # 3. Подготовка списка строк поиска - без изменений
        all_search_lines = search_lines_from_docx
        unique_lines_map = {line.strip().lower(): line.strip() for line in all_search_lines if line.strip()}
        all_search_lines_clean = list(unique_lines_map.values())
        # current_app.logger.info(...)

        # 4. Валидация списка - без изменений
        if not all_search_lines_clean:
            if source_path and os.path.exists(source_path): os.remove(source_path)
            if words_path and os.path.exists(words_path): os.remove(words_path)
            error_msg = 'Файл слов/фраз пуст или не содержит распознаваемых слов/фраз.'
            return render_template('tool_footnotes/index.html', error=error_msg, analyzers_ready=ANALYZERS_READY)

        # --- 5. ИЗМЕНЕННАЯ ПОДГОТОВКА ДАННЫХ ДЛЯ ПОИСКА ---
        prepared_data_unified = prepare_search_terms(all_search_lines_clean)
        search_lemmas_map, search_stems_map = get_footnotes_word_maps(prepared_data_unified)
        search_phrase_lemmas_map, search_phrase_stems_map = get_footnotes_phrase_maps(prepared_data_unified)

        # Проверка, что хоть что-то подготовилось (остается)
        if not search_lemmas_map and not search_stems_map and not search_phrase_lemmas_map and not search_phrase_stems_map:
             if source_path and os.path.exists(source_path): os.remove(source_path)
             if words_path and os.path.exists(words_path): os.remove(words_path)
             error_msg = 'После морфологической обработки не осталось данных для поиска.'
             return render_template('tool_footnotes/index.html', error=error_msg, analyzers_ready=ANALYZERS_READY)

        # 6. ВЫЗОВ СЕРВИСА ОБРАБОТКИ (без изменений, т.к. он принимает те же карты)
        result_filename_base = f"result_highlighted_terms_{timestamp_str}"
        result_filename_docx = f"{result_filename_base}.docx"
        result_path_docx = os.path.join(RESULT_DIR, result_filename_docx)
        result_filename_stats = f"{result_filename_base}{STATS_FILE_SUFFIX}"
        stats_file_path = os.path.join(RESULT_DIR, result_filename_stats)


        analysis_results = analyze_and_process_docx(
            source_path=source_path,
            search_lemmas_map=search_lemmas_map, # Передаем карты, полученные из адаптеров
            search_stems_map=search_stems_map,
            search_phrase_lemmas_map=search_phrase_lemmas_map,
            search_phrase_stems_map=search_phrase_stems_map,
            output_path=result_path_docx
        )


        # 7. Обработка результатов анализа (без изменений)
        if analysis_results is None:
             # current_app.logger.error(...)
             if source_path and os.path.exists(source_path): os.remove(source_path)
             if words_path and os.path.exists(words_path): os.remove(words_path)
             return render_template('tool_footnotes/index.html', error='Ошибка при анализе документа и подсветке терминов.', analyzers_ready=ANALYZERS_READY)

        word_stats = analysis_results.get('word_stats', {})
        phrase_stats = analysis_results.get('phrase_stats', {})
        # current_app.logger.info(...)

        # 8. Проверка создания файла DOCX (без изменений)
        if not os.path.exists(result_path_docx) or not os.path.isfile(result_path_docx):
            # current_app.logger.error(...)
            if source_path and os.path.exists(source_path): os.remove(source_path)
            if words_path and os.path.exists(words_path): os.remove(words_path)
            return render_template('tool_footnotes/index.html', error='Ошибка: файл результата .docx не создан.', analyzers_ready=ANALYZERS_READY)
        # current_app.logger.info(...)

        # 9. Сохранение статистики в JSON (без изменений)
        stats_file_created = False
        try:
            stats_data_to_save = { 'word_stats': word_stats, 'phrase_stats': phrase_stats }
            with open(stats_file_path, 'w', encoding='utf-8') as f_stats:
                json.dump(stats_data_to_save, f_stats, ensure_ascii=False, indent=4)
            # current_app.logger.info(...)
            stats_file_created = True
        except Exception as e:
            # current_app.logger.error(...)
            stats_file_path = None

        processing_duration = round(time.time() - start_time, 2)

        # 10. Сохранение данных в сессию (без изменений)
        session_data = {
            'source_filename': source_file.filename,
            'words_filename': words_filename_for_session,
            'result_filename_docx': result_filename_docx,
            'result_filename_stats': result_filename_stats if stats_file_created else None,
            'processing_time': processing_duration,
        }
        session['last_result_data_footnotes'] = session_data
        # current_app.logger.debug(...)

        # 11. Перенаправление на страницу результатов (без изменений)
        # current_app.logger.info(...)
        return redirect(url_for('footnotes.results'))

    # --- Обработчики ошибок --- (без изменений)
    except FileNotFoundError as e:
        # ...
        return render_template('tool_footnotes/index.html', error=f'Ошибка: Необходимый файл не найден ({e}).', analyzers_ready=ANALYZERS_READY)
    except Exception as e:
        # ...
        traceback_str = traceback.format_exc()
        error_message = f'Произошла внутренняя ошибка сервера при обработке.'
        # if current_app.debug: error_message += f'<br><pre>{traceback_str}</pre>' # Убрал логгер из этой части
        return render_template('tool_footnotes/index.html', error=error_message, analyzers_ready=ANALYZERS_READY)

# Функции results() и download_result(filename) остаются без изменений,
# так как они работают с результатами (статистикой из файла и скачиванием DOCX),
# а не с процессом подготовки данных.

@footnotes_bp.route('/results')
def results():
    # ... (код без изменений) ...
    result_data_session = session.get('last_result_data_footnotes')
    if not result_data_session: return redirect(url_for('footnotes.index'))
    result_filename_docx = result_data_session.get('result_filename_docx')
    result_filename_stats = result_data_session.get('result_filename_stats')
    result_dir = current_app.config.get('RESULT_DIR_FOOTNOTES', current_app.config.get('RESULT_DIR'))
    word_stats = {}; phrase_stats = {}; stats_error = None
    if result_filename_stats:
        stats_file_path = os.path.join(result_dir, result_filename_stats)
        if os.path.exists(stats_file_path) and os.path.isfile(stats_file_path):
            try:
                with open(stats_file_path, 'r', encoding='utf-8') as f_stats:
                    loaded_stats = json.load(f_stats)
                word_stats = loaded_stats.get('word_stats', {})
                phrase_stats = loaded_stats.get('phrase_stats', {})
            except Exception as e:
                stats_error = f"Ошибка чтения файла статистики '{result_filename_stats}': {e}."
        else:
            stats_error = f"Файл статистики '{result_filename_stats}' не найден."
    elif 'result_filename_stats' in result_data_session:
        stats_error = "Файл статистики не был создан во время обработки."
    else:
        stats_error = "Информация о файле статистики отсутствует."
    sorted_word_stats = sorted(word_stats.items(), key=lambda item: item[0])
    sorted_phrase_stats = sorted(phrase_stats.items(), key=lambda item: item[0])
    template_context = {
        'source_filename': result_data_session.get('source_filename'),
        'words_filename': result_data_session.get('words_filename'),
        'result_filename': result_filename_docx,
        'processing_time': result_data_session.get('processing_time'),
        'word_stats': sorted_word_stats, # Переименовал для консистентности с highlight
        'phrase_stats': sorted_phrase_stats, # Переименовал для консистентности с highlight
        'has_results': bool(sorted_word_stats or sorted_phrase_stats),
        'stats_error': stats_error
    }
    return render_template('tool_footnotes/results.html', **template_context)


@footnotes_bp.route('/download-result/<path:filename>')
def download_result(filename):
    # ... (код без изменений) ...
    result_dir = current_app.config.get('RESULT_DIR_FOOTNOTES', current_app.config.get('RESULT_DIR'))
    if not filename or '..' in filename or filename.startswith('/'): return "Недопустимое имя файла.", 400
    filepath_abs = os.path.abspath(os.path.join(result_dir, filename))
    result_dir_abs = os.path.abspath(result_dir)
    if not filepath_abs.startswith(result_dir_abs + os.sep): return "Доступ запрещен.", 403
    if not os.path.exists(filepath_abs) or not os.path.isfile(filepath_abs): return "Файл не найден на сервере.", 404
    try:
        return send_file(filepath_abs, as_attachment=True)
    except Exception as e: return "Ошибка при отправке файла.", 500

# --- END OF FILE tool_footnotes/routes.py --- (ADAPTED)