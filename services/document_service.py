# --- START OF FILE document_service.py ---

import os
import docx # Для работы с .docx файлами
import re   # Для регулярных выражений
import logging # Для логирования
import fitz # PyMuPDF, для работы с .pdf файлами

# --- Настройка логирования ---
logger_ds = logging.getLogger(__name__)
# Установим уровень DEBUG для подробной отладки PDF
# В реальном приложении уровень можно настраивать через конфигурацию
logger_ds.setLevel(logging.DEBUG)
# Добавим обработчик, если его нет (например, при запуске скрипта напрямую)
if not logger_ds.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger_ds.addHandler(handler)


# --- Константы ---
TOKEN_PATTERN = re.compile(r'\b\w+\b', re.UNICODE) # Паттерн для токенизации

# --- Функция для сохранения файлов ---
def save_uploaded_file(file_obj, upload_folder, custom_filename=None):
    """
    Сохраняет загруженный файловый объект в указанную папку.
    """
    if not file_obj or not file_obj.filename:
        logger_ds.error("Попытка сохранить пустой или некорректный file_obj.")
        return None
    filename = custom_filename if custom_filename else file_obj.filename
    filename = os.path.basename(filename) # Безопасность
    if not filename:
        logger_ds.error(f"Не удалось получить безопасное имя файла из: {custom_filename or file_obj.filename}")
        return None
    file_path = os.path.join(upload_folder, filename)
    try:
        os.makedirs(upload_folder, exist_ok=True)
        # Assuming file_obj is a Flask/Werkzeug FileStorage object
        if hasattr(file_obj, 'save') and callable(file_obj.save):
             file_obj.save(file_path)
        else:
             # Fallback for other file-like objects if needed
             with open(file_path, 'wb') as f:
                 # Read in chunks to handle large files
                 chunk_size = 8192
                 while True:
                     chunk = file_obj.read(chunk_size)
                     if not chunk:
                         break
                     f.write(chunk)
        logger_ds.info(f"Файл '{getattr(file_obj, 'filename', 'N/A')}' сохранен как '{file_path}'")
        return file_path
    except Exception as e:
        logger_ds.error(f"Ошибка сохранения файла '{getattr(file_obj, 'filename', 'N/A')}' в '{file_path}': {e}", exc_info=True)
        return None

# --- Функции для DOCX ---
def extract_words_from_docx(file_path, as_text=False):
    """
    Извлекает все слова (токены) или полный текст из файла DOCX.
    """
    logger_ds.debug(f"Извлечение {'текста' if as_text else 'слов'} из DOCX: {file_path}")
    if not os.path.exists(file_path):
        logger_ds.error(f"Файл DOCX не найден для извлечения: {file_path}")
        raise FileNotFoundError(f"Файл DOCX не найден: {file_path}")
    try:
        doc = docx.Document(file_path)
    except Exception as e:
        logger_ds.error(f"Ошибка открытия DOCX документа '{file_path}': {e}", exc_info=True)
        raise IOError(f"Ошибка при открытии документа {file_path}: {str(e)}")

    words = []
    full_text_parts = []
    try:
        for p in doc.paragraphs:
            text = p.text
            if text:
                full_text_parts.append(text)
                if not as_text:
                    words.extend(TOKEN_PATTERN.findall(text))
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    for p_cell in c.paragraphs:
                        text = p_cell.text
                        if text:
                            full_text_parts.append(text)
                            if not as_text:
                                words.extend(TOKEN_PATTERN.findall(text))
    except Exception as e:
        logger_ds.error(f"Ошибка во время обработки содержимого DOCX '{file_path}': {e}", exc_info=True)
        pass # Continue processing if possible, or re-raise if critical
    if as_text:
        result = '\n'.join(full_text_parts)
        logger_ds.debug(f"Извлечен текст DOCX длиной {len(result)} символов.")
        return result
    else:
        logger_ds.debug(f"Извлечено {len(words)} слов из DOCX.")
        return words

def extract_lines_from_docx(file_path):
    """
    Извлекает непустые строки текста из файла DOCX.
    """
    logger_ds.debug(f"Извлечение строк из DOCX: {file_path}")
    if not os.path.exists(file_path):
        logger_ds.error(f"Файл DOCX не найден для извлечения строк: {file_path}")
        raise FileNotFoundError(f"Файл DOCX не найден: {file_path}")
    lines = []
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text: lines.append(text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        text = paragraph.text.strip()
                        if text: lines.append(text)
        logger_ds.debug(f"Извлечено {len(lines)} строк из DOCX.")
        return lines
    except Exception as e:
        logger_ds.error(f"Ошибка при извлечении строк из DOCX '{file_path}': {e}", exc_info=True)
        return []


# --- НОВАЯ ФУНКЦИЯ ФИЛЬТРАЦИИ (как мы обсуждали) ---
HAS_ANY_LETTER_PATTERN = re.compile(r'[a-zA-Zа-яА-ЯёЁ]')

def is_predominantly_non_alphabetic(text_segment, min_letter_ratio=0.5):
    if not text_segment or not isinstance(text_segment, str):
        return True
    stripped_text = text_segment.strip()
    if not stripped_text:
        return True
    letters_found = HAS_ANY_LETTER_PATTERN.findall(stripped_text)
    num_letters = len(letters_found)
    total_len = len(stripped_text)
    if total_len == 0: return True
    letter_ratio = num_letters / total_len
    if letter_ratio < min_letter_ratio:
        logger_ds.debug(f"Marked as garbage: '{text_segment}', Ratio={letter_ratio:.2f} < {min_letter_ratio}")
        return True
    return False
# --- КОНЕЦ НОВОЙ ФУНКЦИИ ---


# --- Функция для склейки слов ВНУТРИ блока ---
def extract_logical_words_from_block(block_words, block_rect):
    """
    Склеивает переносы ТОЛЬКО ПО ДЕФИСУ.
    Возвращает 'rects' как список кортежей координат [(x0,y0,x1,y1), ...].
    """
    logical_words_in_block = []
    # --- Параметры ---
    VERTICAL_TOLERANCE = 5.0
    MIN_LINE_JUMP = 8.0
    MIN_WORD_PART_LEN = 2

    i = 0
    num_words = len(block_words)
    while i < num_words:
        current_word_info = block_words[i]
        try:
            # Ожидаем: x0, y0, x1, y1, text, block_no, line_no, word_no, page_num
            x0, y0, x1, y1, current_text_raw, _, _, _, _ = current_word_info
        except ValueError:
             logger_ds.error(f"Ошибка распаковки word_info: {current_word_info}", exc_info=False)
             i += 1
             continue

        current_text = current_text_raw.strip()

        # Проверка текста и базовых координат
        if not current_text or x0 >= x1 or y0 >= y1:
            # logger_ds.warning(f"Пропуск слова из-за текста или невалидных координат: Text='{current_text}', Coords=({x0},{y0},{x1},{y1})") # Можно раскомментировать для отладки
            i += 1
            continue

        # Координаты текущего слова (как кортеж)
        current_coords = (x0, y0, x1, y1)

        # ... (код проверки дефиса и очистки cleaned_current_text) ...
        potential_hyphen_removed = False
        cleaned_current_text = current_text
        hyphen_chars = '-\u2010\u2013\u2014\u00AD' # Hyphen, Non-Breaking Hyphen, En Dash, Em Dash, Soft Hyphen
        if current_text.endswith(tuple(hyphen_chars)):
            temp_cleaned = current_text.rstrip(hyphen_chars)
            # Только если после удаления дефиса что-то осталось
            if temp_cleaned:
                cleaned_current_text = temp_cleaned
                potential_hyphen_removed = True

        found_merge = False
        if i + 1 < num_words:
            next_word_info = block_words[i+1]
            try:
                # Ожидаем: nx0, ny0, nx1, ny1, next_text_raw, _, _, _, _
                nx0, ny0, nx1, ny1, next_text_raw, _, _, _, _ = next_word_info
            except ValueError:
                 logger_ds.error(f"Ошибка распаковки next_word_info: {next_word_info}", exc_info=False)
                 # --- ИЗМЕНЕНИЕ 1: Добавляем кортеж координат ---
                 # Добавляем текущее слово, так как следующее обработать не можем
                 logical_words_in_block.append({'text': cleaned_current_text, 'rects': [current_coords]})
                 i += 1
                 continue

            next_text = next_text_raw.strip()

            # Проверяем текст и координаты следующего слова
            if next_text and nx0 < nx1 and ny0 < ny1:
                # Геометрия
                is_vertically_close = abs(y0 - ny0) < VERTICAL_TOLERANCE # На одной строке?
                is_next_line_below = ny0 > y0 + MIN_LINE_JUMP # Следующее слово ощутимо ниже?
                # Длина частей слова
                is_long_enough = len(cleaned_current_text) >= MIN_WORD_PART_LEN and len(next_text) >= MIN_WORD_PART_LEN
                # Условие склейки: есть дефис, следующее слово ниже, обе части достаточно длинные
                condition1_hyphen = potential_hyphen_removed and is_next_line_below and is_long_enough

                # Склеиваем только если не на одной строке и условие дефиса выполнено
                if not is_vertically_close and condition1_hyphen:
                    # --- ИЗМЕНЕНИЕ 2: Добавляем оба кортежа координат ---
                    next_coords = (nx0, ny0, nx1, ny1)
                    merged_text = cleaned_current_text + next_text
                    logical_words_in_block.append({'text': merged_text, 'rects': [current_coords, next_coords]})
                    # Используем переданный block_rect для логирования контекста блока
                    logger_ds.info(f"    Блок {block_rect}: >>> СКЛЕЕНО (Дефис): '{current_text_raw}' + '{next_text_raw}' -> '{merged_text}'")
                    i += 2 # Пропускаем и текущее, и следующее слово
                    found_merge = True
                # Логируем, почему не склеили (если был дефис, но другое условие не сошлось)
                elif not is_vertically_close and potential_hyphen_removed:
                    reasons = []
                    if not is_next_line_below: reasons.append("ДефисНоНеНиже")
                    if not is_long_enough: reasons.append("ДефисНоКоротко")
                    # if is_vertically_close: reasons.append("ДефисНоНаТойЖеСтроке?") # Эта проверка уже есть во внешнем if
                    if not reasons: reasons.append("Неизвестно")
                    # logger_ds.debug(f"    Блок {block_rect}: Склейка по дефису НЕ выполнена для '{current_text_raw}' + '{next_text_raw}'. Причины: {', '.join(reasons)}") # Раскомментировать для детальной отладки
                    pass # Логирование причин несклейки

            # Сюда попадаем, если у следующего слова нет текста ИЛИ некорректные координаты
            elif next_text: # Текст есть, значит координаты некорректны
                 # logger_ds.warning(f"Пропуск след. слова из-за невалидных координат: Text='{next_text}', Coords=({nx0},{ny0},{nx1},{ny1})") # Раскомментировать для детальной отладки
                 pass # Просто не склеиваем
            # Если и текста нет (next_text пуст), то ничего не делаем, просто не будем склеивать


        if not found_merge:
            # --- ИЗМЕНЕНИЕ 3: Добавляем кортеж координат ---
            # Добавляем текущее слово с его координатами, если не было склейки
            logical_words_in_block.append({'text': cleaned_current_text, 'rects': [current_coords]})
            i += 1 # Переходим к следующему слову

    return logical_words_in_block


# --- Основная функция извлечения из PDF ---
def extract_all_logical_words_from_pdf(pdf_path):
    """
    Извлекает все логические слова из ВСЕХ блоков на ВСЕХ страницах PDF.
    Возвращает список списков (страницы -> слова), где каждое слово - словарь
    {'text': str, 'rects': [(x0,y0,x1,y1), ...]}.
    Возвращает None в случае ошибки.
    Включает проверку координат перед созданием Rect для блоков.
    Использует обновленный extract_logical_words_from_block.
    Добавлена фильтрация "мусорных" слов с помощью is_predominantly_non_alphabetic.
    """
    all_pages_logical_words = []
    doc = None
    logger_ds.info(f"Начало извлечения лог. слов из PDF (с проверкой коорд. и фильтрацией мусора): {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
        logger_ds.debug(f"Открыт PDF, страниц: {len(doc)}")
        all_words_data_raw = [] # Собираем сырые данные слов
        all_blocks_data_raw = [] # Собираем сырые данные блоков

        # 1. Собираем сырые данные слов и блоков со всех страниц
        for page_num in range(len(doc)):
             page = doc.load_page(page_num)
             # Получаем слова: x0, y0, x1, y1, text, block_no, line_no, word_no
             words_on_page = page.get_text("words", sort=True)
             # Получаем блоки: bx0, by0, bx1, by1, text, block_no, block_type (0 текст, 1 картинка)
             blocks_on_page = page.get_text("blocks", sort=True)
             # Добавляем номер страницы к каждому элементу для последующей фильтрации
             for w in words_on_page: all_words_data_raw.append(list(w) + [page_num]) # page_num будет индекс 8
             for b in blocks_on_page: all_blocks_data_raw.append(list(b) + [page_num]) # page_num будет индекс 7

        # 2. Обрабатываем блоки и слова постранично
        for page_num in range(len(doc)):
            logger_ds.debug(f"--- Обработка страницы {page_num + 1} ---")
            logical_words_on_page = []
            # Фильтруем блоки и слова для текущей страницы по их номеру страницы
            current_page_blocks = [b for b in all_blocks_data_raw if b[7] == page_num]
            current_page_words_raw = [w for w in all_words_data_raw if w[8] == page_num]

            for block_data in current_page_blocks:
                # Проверяем тип блока (0 - текст)
                block_type = block_data[6]
                if block_type != 0:
                    # logger_ds.debug(f"  Пропуск нетекстового блока {block_data[5]} (Тип {block_type})")
                    continue # Пропускаем нетекстовые блоки (например, картинки)

                # Распаковываем данные блока
                # bx0, by0, bx1, by1, text_in_block, block_no, block_type, page_num_block
                bx0, by0, bx1, by1, _, block_no, _, _ = block_data
                # Проверяем координаты блока перед созданием Rect
                if bx0 >= bx1 or by0 >= by1:
                    logger_ds.warning(f"Пропуск блока {block_no} на стр. {page_num+1} из-за невалидных координат: ({bx0},{by0},{bx1},{by1})")
                    continue
                try:
                    # Создаем Rect блока в основном для логирования и отладки
                    block_rect_for_logging = fitz.Rect(bx0, by0, bx1, by1)
                    logger_ds.debug(f"  Обработка блока {block_no} (Тип {block_type}) с Rect: {block_rect_for_logging}")
                except Exception as e_rect_block:
                    logger_ds.warning(f"  Ошибка создания Rect для блока {block_no} на стр. {page_num+1}: {e_rect_block}. Пропуск блока.")
                    continue # Пропускаем блок, если не удалось создать Rect

                # Выбираем слова, принадлежащие этому блоку (геометрически)
                # Используем небольшую погрешность epsilon, чтобы включить слова на границе
                epsilon = 1.0
                words_in_this_block_raw = [
                    w for w in current_page_words_raw
                    # Слово w: x0, y0, x1, y1, text, block_no, line_no, word_no, page_num_word
                    # Проверяем, что геометрия слова находится внутри (или очень близко) геометрии блока
                    if w[0] >= bx0 - epsilon and w[1] >= by0 - epsilon and
                       w[2] <= bx1 + epsilon and w[3] <= by1 + epsilon
                ]

                # Сортируем слова внутри блока по номеру строки (индекс 6), затем номеру слова (индекс 7)
                words_in_this_block_raw.sort(key=lambda w: (w[6], w[7]))

                logger_ds.debug(f"    Найдено {len(words_in_this_block_raw)} сырых слов в блоке {block_no}.")
                if words_in_this_block_raw:
                    # Вызываем обновленный extract_logical_words_from_block,
                    # который вернет список словарей {'text':..., 'rects': [(x0,y0,x1,y1),...]}
                    # Передаем Rect блока для возможного использования в логах внутри функции
                    logical_words_from_block_extraction = extract_logical_words_from_block(words_in_this_block_raw, block_rect_for_logging)
                    
                    # --- НАЧАЛО ИЗМЕНЕНИЯ: Фильтрация "мусорных" слов ---
                    filtered_logical_words_for_block = []
                    for logical_word_dict in logical_words_from_block_extraction:
                        text_to_check = logical_word_dict.get('text', '')
                        # Применяем фильтр: если слово НЕ является преимущественно неалфавитным, добавляем его
                        if not is_predominantly_non_alphabetic(text_to_check):
                            filtered_logical_words_for_block.append(logical_word_dict)
                        else:
                            # Логируем, что слово было отфильтровано как "мусорное"
                            logger_ds.debug(f"    Отфильтровано логическое слово из блока {block_no} (стр. {page_num+1}) из-за содержимого: '{text_to_check}'")
                    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
                    
                    if filtered_logical_words_for_block: # Добавляем только если после фильтрации что-то осталось
                        logical_words_on_page.extend(filtered_logical_words_for_block)
                        logger_ds.debug(f"    Добавлено {len(filtered_logical_words_for_block)} (после фильтрации) лог. слов из блока {block_no}.")


            all_pages_logical_words.append(logical_words_on_page)
            logger_ds.debug(f"--- Страница {page_num + 1}: Собрано {len(logical_words_on_page)} логических слов (после фильтрации) ---")

        logger_ds.info(f"Завершено извлечение логических слов из PDF (с фильтрацией).")
        return all_pages_logical_words

    except Exception as e_general: # Ловим общее исключение на уровне всей функции
        logger_ds.error(f"Критическая ошибка при извлечении лог. слов из PDF '{pdf_path}': {e_general}", exc_info=True)
        return None # Возвращаем None при любой серьезной ошибке

    finally:
        if doc:
            try:
                doc.close()
                logger_ds.debug(f"PDF документ {pdf_path} закрыт.")
            except Exception as e_close:
                 # Логируем, но не прерываем выполнение, если закрытие не удалось
                 logger_ds.warning(f"Не удалось корректно закрыть PDF документ {pdf_path}: {e_close}")

# --- END OF FILE document_service.py ---