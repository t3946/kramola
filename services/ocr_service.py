# --- START OF FILE services/ocr_service.py ---

import os
import pymupdf
import pytesseract
from PIL import Image
import io
import logging
import pandas as pd # Для парсинга вывода tesseract
import time
import re # Импортирован re для использования регулярных выражений
import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

logger_ocr = logging.getLogger(__name__)

# Паттерн для удаления ведущих/завершающих не-буквенно-цифровых символов
# \w включает буквы (во всех языках Unicode), цифры и знак подчеркивания.
# Используется для очистки текста *перед* лемматизацией.
PUNCT_STRIP_PATTERN_OCR = re.compile(r"^[^\w]+|[^\w]+$", re.UNICODE)

# --- Конфигурация ---
# Укажите путь к исполняемому файлу tesseract, если он не в системном PATH
tesseract_path = os.environ.get('TESSERACT_PATH')

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Языки для распознавания (должны быть установлены!)
OCR_LANGUAGES = 'rus+eng'
# DPI для рендеринга страницы в изображение
OCR_DPI = 300
# Минимальная уверенность OCR слова для его дальнейшей обработки
MIN_OCR_WORD_CONFIDENCE = 10 # Можно поднять, если много мусора
# Дефис для поиска переносов
HYPHEN_CHAR = '-'

# --- Новая функция для обработки переносов ---
def _handle_hyphenation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Пост-обработка DataFrame Tesseract для объединения слов с переносами.

    Args:
        df (pd.DataFrame): DataFrame с результатами Tesseract после базовой очистки.

    Returns:
        pd.DataFrame: DataFrame с объединенными словами.
    """
    if df is None or df.empty or not all(c in df.columns for c in ['level', 'text', 'block_num', 'par_num', 'line_num', 'word_num', 'conf', 'left', 'top', 'width', 'height']):
        logger_ocr.debug("Пропуск обработки переносов: DataFrame пуст или отсутствуют необходимые колонки.")
        return df

    # Убедимся, что 'text' - это строка
    df['text'] = df['text'].astype(str)

    # Отбираем только слова
    words_df = df[df['level'] == 5].copy()
    if words_df.empty:
        logger_ocr.debug("Пропуск обработки переносов: нет слов (level 5).")
        return df

    # Индексы строк для удаления (исходные части переносов)
    indices_to_drop = set()
    # Список для новых, объединенных строк
    merged_rows = []

    # Используем итератор, который дает доступ к следующей строке
    word_iterator = words_df.itertuples()
    try:
        current_word = next(word_iterator)
    except StopIteration:
        return df # Нет слов

    while True:
        try:
            next_word = next(word_iterator)

            # Проверка на перенос
            # 1. Текущее слово заканчивается на дефис (и не состоит только из него)
            # 2. Следующее слово - первое на следующей строке в том же параграфе/блоке
            if (current_word.text.endswith(HYPHEN_CHAR) and len(current_word.text) > 1 and
                    next_word.block_num == current_word.block_num and
                    next_word.par_num == current_word.par_num and
                    next_word.line_num == current_word.line_num + 1 and
                    next_word.word_num == 1): # Является ли оно первым словом? (Tesseract нумерует с 1)

                text1 = current_word.text[:-len(HYPHEN_CHAR)] # Текст без дефиса
                text2 = next_word.text

                # Создаем объединенную запись
                merged_text = text1 + text2
                # Используем координаты первой части для простоты, можно улучшить (union rect)
                merged_left = current_word.left
                merged_top = current_word.top
                # Ширина - от начала первой части до конца второй части
                merged_width = (next_word.left + next_word.width) - current_word.left
                # Высота - максимальная из двух частей (приблизительно)
                merged_height = max(current_word.height, next_word.height)
                # Уверенность - минимальная из двух частей (консервативно)
                merged_conf = min(current_word.conf, next_word.conf)

                merged_row = {
                    'level': 5, # Сохраняем уровень слова
                    'page_num': current_word.page_num,
                    'block_num': current_word.block_num,
                    'par_num': current_word.par_num,
                    'line_num': current_word.line_num, # Оставляем номер строки первой части
                    'word_num': current_word.word_num, # Оставляем номер слова первой части
                    'left': merged_left,
                    'top': merged_top,
                    'width': merged_width,
                    'height': merged_height,
                    'conf': merged_conf,
                    'text': merged_text
                    # Другие колонки Tesseract можно либо проигнорировать, либо взять из первой части
                }
                merged_rows.append(merged_row)
                logger_ocr.debug(f"Объединен перенос: '{current_word.text}' + '{next_word.text}' -> '{merged_text}' (conf: {merged_conf:.2f})")

                # Добавляем индексы обеих частей для удаления
                indices_to_drop.add(current_word.Index)
                indices_to_drop.add(next_word.Index)

                # Пропускаем next_word, так как он уже обработан
                current_word = next(word_iterator)
                if current_word is None: break # Достигли конца

            else:
                # Если переноса нет, просто переходим к следующему слову
                current_word = next_word

        except StopIteration:
            # Достигли конца итератора
            break
        except Exception as e_iter:
            # Ошибка при итерации
            logger_ocr.error(f"Ошибка при обработке переноса: {e_iter}. Строка: {getattr(current_word, 'Index', 'N/A')}", exc_info=True)
            # Попытаемся перейти к следующему слову, чтобы не завесить процесс
            try:
                current_word = next(word_iterator)
            except StopIteration:
                 break
            except Exception: # Если и следующая ошибка, выходим
                 logger_ocr.error("Повторная ошибка итерации при обработке переносов, прекращаем.")
                 break


    # Собираем результат
    if indices_to_drop:
        logger_ocr.info(f"Обработано переносов (объединено): {len(merged_rows)}")
        # Удаляем исходные части
        df_original_kept = df.drop(index=list(indices_to_drop))
        # Создаем DataFrame из объединенных строк
        df_merged = pd.DataFrame(merged_rows)
        # Объединяем DataFrame-ы
        # Используем ignore_index=True для пересоздания индекса
        result_df = pd.concat([df_original_kept, df_merged], ignore_index=True)
        # Важно: отсортировать обратно по позиции, если порядок важен
        # Сортировка по блоку, параграфу, строке, номеру слова
        result_df = result_df.sort_values(by=['block_num', 'par_num', 'line_num', 'word_num'], ascending=True)
        logger_ocr.debug(f"DataFrame после обработки переносов: {len(result_df)} строк.")
        return result_df
    else:
        logger_ocr.debug("Переносы для объединения не найдены.")
        return df # Возвращаем исходный, если ничего не изменилось

# --- Основная функция OCR (модифицированная) ---
def ocr_page(page: pymupdf.Page, languages: str = OCR_LANGUAGES, dpi: int = OCR_DPI):
    """
    Выполняет OCR для одной страницы PDF, применяя предобработку OpenCV
    и обработку переносов строк.

    Args:
        page: Объект страницы pymupdf.Page.
        languages: Строка с языками для Tesseract (например, 'rus+eng').
        dpi: Разрешение для рендеринга страницы в изображение.

    Returns:
        pandas.DataFrame: DataFrame с результатами OCR (level, page_num, block_num, ..., text, conf)
                          с предобработкой, обработкой переносов и очисткой, или None в случае ошибки.
                          Колонки приведены к ожидаемым типам.
        pymupdf.Matrix: Матрица преобразования, использованная для рендеринга.
        tuple: Размеры изображения (width, height) или None.
    """
    logger_ocr.info(f"Запуск OCR для страницы {page.number + 1} (Языки: {languages}, DPI: {dpi}) с OpenCV и обработкой переносов") # Обновлено сообщение
    start_time = time.time()
    ocr_results_df = None
    img_pil = None # PIL Image для Tesseract
    pix = None
    img_size = None
    matrix = None # Инициализируем матрицу

    try:
        # Создаем матрицу масштабирования
        matrix = pymupdf.Matrix(dpi / 72.0, dpi / 72.0)
    except Exception as e_matrix:
        logger_ocr.error(f"Ошибка создания матрицы масштабирования: {e_matrix}")
        return None, None, None

    try:
        # 1. Рендеринг страницы в изображение (Pixmap)
        # ... (код рендеринга и предобработки OpenCV остается без изменений) ...
        logger_ocr.debug(f"Рендеринг страницы {page.number + 1} в изображение...")
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_size = (pix.width, pix.height)
        img_bytes = pix.tobytes("png")
        if not img_bytes:
             logger_ocr.warning(f"Не удалось получить байты изображения со стр. {page.number + 1}")
             return None, matrix, img_size
        logger_ocr.debug(f"Изображение создано: {img_size[0]}x{img_size[1]}.")

        # --- 2. Предобработка с OpenCV ---
        processed_image_bytes = None
        try:
            # ... (код OpenCV остается без изменений) ...
            logger_ocr.debug("Запуск предобработки OpenCV...")
            nparr = np.frombuffer(img_bytes, np.uint8)
            cv_img_gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            if cv_img_gray is None: raise ValueError("cv2.imdecode не смог декодировать изображение.")
            blockSize = 11; C = 2
            processed_cv_img = cv2.adaptiveThreshold(cv_img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize, C)
            is_success, buffer = cv2.imencode(".png", processed_cv_img)
            if not is_success: raise ValueError("cv2.imencode не смог закодировать обработанное изображение.")
            processed_image_bytes = buffer.tobytes()
            logger_ocr.debug("OpenCV: Предобработка завершена.")
            # --- Сохранение отладочного изображения ---
            try:
                debug_save_path = f'ocr_debug_processed_page_{page.number + 1}.png'
                with open(debug_save_path, "wb") as f_debug: f_debug.write(processed_image_bytes)
                logger_ocr.info(f"DEBUG: ОБРАБОТАННОЕ изображение сохранено в {debug_save_path}")
            except Exception as e_save: logger_ocr.warning(f"DEBUG: Не удалось сохранить обработанное изображение: {e_save}")
        except ImportError:
             logger_ocr.error("Библиотеки OpenCV или NumPy не найдены! Используем исходное изображение.")
             processed_image_bytes = img_bytes
        except Exception as e_cv:
            logger_ocr.error(f"Ошибка во время OpenCV обработки стр. {page.number + 1}: {e_cv}. Используем исходное изображение.", exc_info=True)
            processed_image_bytes = img_bytes

        # Создаем PIL Image
        if processed_image_bytes:
            try:
                img_pil = Image.open(io.BytesIO(processed_image_bytes))
                logger_ocr.debug("Создан PIL Image для Tesseract.")
            except Exception as e_pil:
                logger_ocr.error(f"Не удалось создать PIL Image из байт: {e_pil}")
                return None, matrix, img_size
        else:
             logger_ocr.error("Байты изображения для PIL Image отсутствуют.")
             return None, matrix, img_size

        # 3. Запуск Tesseract OCR
        logger_ocr.debug(f"Вызов pytesseract.image_to_data (языки: {languages}, --psm 3)...") # <-- ИЗМЕНЕНО НА --psm 3 (обычно лучше для общего текста)
        # Попробуйте --psm 3 для лучшего определения структуры (блоков, параграфов, строк)
        ocr_results_df = pytesseract.image_to_data(
            img_pil,
            lang=languages,
            output_type=pytesseract.Output.DATAFRAME,
            config='--psm 11' # <--- ИЗМЕНЕНО НА 3 (Автоматическое сегментирование)
        )
        logger_ocr.debug("Tesseract image_to_data выполнен.")

        # --- Логирование сырого вывода ---
        # ... (код логирования остается) ...
        log_prefix = f"RAW OCR (Processed) стр. {page.number + 1}:"
        if ocr_results_df is None: logger_ocr.warning(f"{log_prefix} Tesseract вернул None!")
        elif ocr_results_df.empty: logger_ocr.warning(f"{log_prefix} Tesseract вернул ПУСТОЙ DataFrame.")
        else:
            logger_ocr.info(f"{log_prefix} Tesseract вернул DataFrame ({len(ocr_results_df)} строк). Первые строки:")
            try: logger_ocr.info("\n" + ocr_results_df.head(15).to_string())
            except Exception as e_log: logger_ocr.error(f"{log_prefix} Ошибка при логировании DataFrame: {e_log}")

        # --- 4. Базовая очистка DataFrame Tesseract ---
        if ocr_results_df is None or ocr_results_df.empty:
            logger_ocr.info(f"Нет данных от Tesseract для стр. {page.number+1} или они пустые.")
            return pd.DataFrame(), matrix, img_size

        try:
            # Приведение числовых колонок к числовому типу, заменяя нечисловые на NaN
            num_cols = ['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf']
            for col in num_cols:
                if col in ocr_results_df.columns:
                    ocr_results_df[col] = pd.to_numeric(ocr_results_df[col], errors='coerce')
                else:
                    logger_ocr.warning(f"Ожидаемая колонка '{col}' отсутствует в выводе Tesseract. Заполняем NaN.")
                    ocr_results_df[col] = np.nan # Используем NaN для отсутствующих числовых

            # Удаляем строки, где ключевые структурные или координатные данные отсутствуют (стали NaN)
            ocr_results_df.dropna(subset=['level', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf'], inplace=True)

            # Приведение к int после удаления NaN
            int_cols = ['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height']
            for col in int_cols:
                 ocr_results_df[col] = ocr_results_df[col].astype(int)

            ocr_results_df['conf'] = ocr_results_df['conf'].astype(float)

            # Фильтруем строки с отрицательной уверенностью (-1 обычно означает не слово)
            # Уберем это из базовой очистки, чтобы обработчик переносов получил все данные
            # ocr_results_df = ocr_results_df[ocr_results_df['conf'] >= 0]

            # Очистка текста (пробелы) и удаление пустых строк ПОСЛЕ очистки
            ocr_results_df['text'] = ocr_results_df['text'].astype(str).str.strip()
            ocr_results_df.dropna(subset=['text'], inplace=True) # Удаляем строки с NaN текстом (хотя это маловероятно после astype(str))
            ocr_results_df = ocr_results_df[ocr_results_df['text'].str.len() > 0] # Удаляем строки с пустым текстом

            logger_ocr.debug(f"Базовая очистка Tesseract DF завершена, строк: {len(ocr_results_df)}.")

            if ocr_results_df.empty:
                logger_ocr.info(f"Нет валидных данных после базовой очистки для стр. {page.number+1}.")
                return pd.DataFrame(), matrix, img_size

        except KeyError as e:
             logger_ocr.error(f"Ошибка базовой обработки DataFrame Tesseract: отсутствует колонка {e}.")
             return None, matrix, img_size
        except Exception as e_df_base:
             logger_ocr.error(f"Неожиданная ошибка при базовой обработке DataFrame Tesseract: {e_df_base}", exc_info=True)
             return None, matrix, img_size
        # --- Конец базовой очистки DF ---

        # --- 5. Обработка переносов ---
        try:
            logger_ocr.debug("Запуск обработки переносов...")
            ocr_results_df = _handle_hyphenation(ocr_results_df)
            logger_ocr.debug("Обработка переносов завершена.")
        except Exception as e_hyphen:
            logger_ocr.error(f"Ошибка во время обработки переносов: {e_hyphen}", exc_info=True)
            # Продолжаем без обработки переносов, если она упала

        # --- 6. Финальная фильтрация и очистка ---
        try:
            # Фильтруем строки с отрицательной уверенностью ТЕПЕРЬ
            ocr_results_df = ocr_results_df[ocr_results_df['conf'] >= 0]

            # Фильтруем слова по уверенности
            ocr_results_df = ocr_results_df[
                 (ocr_results_df['level'] != 5) | (ocr_results_df['conf'] >= MIN_OCR_WORD_CONFIDENCE)
            ]

            if ocr_results_df.empty:
                logger_ocr.info(f"OCR для стр. {page.number+1}: Не найдено слов/строк с conf >= {MIN_OCR_WORD_CONFIDENCE} после финальной фильтрации.")
                return pd.DataFrame(), matrix, img_size

            # Убедимся, что все нужные колонки все еще int/float после конкатенации
            num_cols_final = ['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height']
            for col in num_cols_final:
                if col in ocr_results_df.columns:
                     ocr_results_df[col] = pd.to_numeric(ocr_results_df[col], errors='coerce').fillna(0).astype(int)
                else: # Если колонки пропали после обработки переносов - добавляем
                     logger_ocr.warning(f"Колонка '{col}' отсутствует ПОСЛЕ обработки переносов. Добавляем с нулями.")
                     ocr_results_df[col] = 0
            ocr_results_df['conf'] = pd.to_numeric(ocr_results_df['conf'], errors='coerce').fillna(0).astype(float)

            logger_ocr.info(f"OCR для стр. {page.number + 1}: Финальная очистка DF завершена, строк: {len(ocr_results_df)}. Общее время: {time.time() - start_time:.2f} сек.")

        except Exception as e_df_final:
             logger_ocr.error(f"Неожиданная ошибка при финальной обработке DataFrame Tesseract: {e_df_final}", exc_info=True)
             return None, matrix, img_size
        # --- Конец финальной очистки DF ---


    # --- Обработка глобальных ошибок ---
    except pytesseract.TesseractNotFoundError:
        logger_ocr.critical("ОШИБКА: Tesseract не найден!")
        raise
    except ImportError:
         logger_ocr.critical("ОШИБКА: Не установлены pytesseract, Pillow, OpenCV или NumPy!")
         raise
    except Exception as e:
        logger_ocr.error(f"Общая ошибка во время OCR страницы {page.number + 1}: {e}", exc_info=True)
        return None, matrix, img_size
    finally:
        if img_pil:
            try: img_pil.close()
            except Exception: pass

    return ocr_results_df, matrix, img_size

# --- Остальные функции (get_lemmas_from_ocr_text, find_ocr_candidates_for_highlight) остаются без изменений ---
# Они будут работать с DataFrame, где переносы уже обработаны.

def get_lemmas_from_ocr_text(ocr_df, pymorphy_lemma_func):
    """
    Добавляет леммы к DataFrame с результатами OCR, очищая текст перед лемматизацией.
    (Без изменений)
    """
    expected_cols = [
        'level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num',
        'left', 'top', 'width', 'height', 'conf', 'text', 'lemma'
    ]
    if ocr_df is None or ocr_df.empty:
        logger_ocr.debug("DataFrame для лемматизации пуст или None.")
        return pd.DataFrame(columns=expected_cols)
    if 'text' not in ocr_df.columns:
        logger_ocr.error("Колонка 'text' отсутствует в DataFrame для лемматизации.")
        ocr_df['lemma'] = None
        for col in expected_cols:
            if col not in ocr_df.columns: ocr_df[col] = None
        return ocr_df.reindex(columns=expected_cols)

    def get_lemma_with_log(text):
        if not isinstance(text, str): return None
        original_text = text.strip()
        if not original_text: return None
        cleaned_text = PUNCT_STRIP_PATTERN_OCR.sub('', original_text)
        if original_text != cleaned_text:
            logger_ocr.debug(f"OCR Text Clean: '{original_text}' -> '{cleaned_text}'")
        cleaned_text_lower = cleaned_text.lower() if cleaned_text else None
        lemma = pymorphy_lemma_func(cleaned_text_lower, use_cache=True) if cleaned_text_lower else None
        #if cleaned_text and cleaned_text.lower() == "шульман": # Пример
        #    logger_ocr.info(f"OCR Lemma Check: Cleaned='{cleaned_text}', Lemma Result='{lemma}'")
        return lemma

    logger_ocr.debug(f"Запуск лемматизации для {len(ocr_df)} OCR строк...")
    start_lemma_time = time.time()
    ocr_df['lemma'] = ocr_df['text'].apply(get_lemma_with_log)
    end_lemma_time = time.time()
    logger_ocr.debug(f"Лемматизация OCR завершена за {end_lemma_time - start_lemma_time:.2f} сек.")

    for col in expected_cols:
        if col not in ocr_df.columns: ocr_df[col] = None
    return ocr_df.reindex(columns=expected_cols)


def find_ocr_candidates_for_highlight(ocr_df_with_lemmas, search_lemmas_set, page_matrix, page_rect, existing_highlight_rects):
    """
    Находит слова из OCR (level=5), которые нужно подсветить...
    (Без изменений)
    """
    candidates = []
    if ocr_df_with_lemmas is None or ocr_df_with_lemmas.empty: return candidates
    if not search_lemmas_set: return candidates
    required_cols = ['level', 'lemma', 'left', 'top', 'width', 'height', 'text', 'conf']
    if not all(col in ocr_df_with_lemmas.columns for col in required_cols):
         missing_cols = [col for col in required_cols if col not in ocr_df_with_lemmas.columns]
         logger_ocr.error(f"DataFrame OCR не содержит необходимых колонок: {missing_cols}.")
         return candidates

    try:
        if abs(page_matrix.det) < 1e-6:
             logger_ocr.error("Матрица страницы вырождена, невозможно инвертировать.")
             return candidates
        inverse_matrix = ~page_matrix
    except ValueError as e_inv:
         logger_ocr.error(f"Не удалось инвертировать матрицу страницы: {e_inv}")
         return candidates

    try:
        word_candidates_df = ocr_df_with_lemmas[
            (ocr_df_with_lemmas['level'] == 5) & \
            (ocr_df_with_lemmas['lemma'].notna()) & \
            (ocr_df_with_lemmas['lemma'].apply(lambda x: isinstance(x, str))) & \
            (ocr_df_with_lemmas['lemma'].isin(search_lemmas_set))
        ].copy()
    except Exception as e_filter:
        logger_ocr.error(f"Ошибка при фильтрации кандидатов OCR: {e_filter}", exc_info=True)
        return candidates

    logger_ocr.debug(f"Найдено {len(word_candidates_df)} потенциальных OCR слов (level=5, lemma in search_set) до проверки геометрии.")

    for index, row in word_candidates_df.iterrows():
        try:
            img_x, img_y = int(row['left']), int(row['top'])
            img_w, img_h = int(row['width']), int(row['height'])
            text, lemma = str(row['text']), row['lemma']
            conf = float(row['conf'])

            if img_w <= 0 or img_h <= 0:
                # logger_ocr.debug(f"Пропуск OCR '{text}': невалидные размеры ({img_w}x{img_h})")
                continue

            img_rect = pymupdf.Rect(img_x, img_y, img_x + img_w, img_y + img_h)
            pdf_rect = img_rect * inverse_matrix
            pdf_rect.normalize()
            if page_rect and not page_rect.is_empty: pdf_rect = pdf_rect & page_rect
            else: logger_ocr.warning(f"Границы страницы PDF (page_rect) невалидны ({page_rect}), pdf_rect не будет ограничен.")

            if not pdf_rect or pdf_rect.is_empty or pdf_rect.width < 1e-3 or pdf_rect.height < 1e-3:
                # logger_ocr.debug(f"Пропуск OCR '{text}': невалидный pdf_rect ({pdf_rect}) после преобразования/пересечения со страницей.")
                continue

            overlaps = False
            expansion_x = max(1.0, pdf_rect.width * 0.05)
            expansion_y = max(1.0, pdf_rect.height * 0.10)
            check_rect = pymupdf.Rect(pdf_rect.x0 - expansion_x, pdf_rect.y0 - expansion_y,
                                   pdf_rect.x1 + expansion_x, pdf_rect.y1 + expansion_y)

            for existing_rect in existing_highlight_rects:
                if not existing_rect or existing_rect.is_empty: continue
                intersection = check_rect & existing_rect
                if not intersection.is_empty and intersection.width > 1e-3 and intersection.height > 1e-3:
                    # logger_ocr.debug(f"Пропуск OCR '{text}' (Rect: {pdf_rect}): пересекается с {existing_rect}.")
                    overlaps = True
                    break

            if not overlaps:
                if pdf_rect and not pdf_rect.is_empty:
                    candidates.append({'text': text, 'lemma': lemma, 'pdf_rect': pdf_rect, 'conf': conf})
                    logger_ocr.debug(f"Добавлен кандидат OCR: '{text}' (Лемма: {lemma}), Rect: {pdf_rect}, Conf: {conf:.2f}")
                else:
                    logger_ocr.warning(f"Не удалось добавить кандидата OCR '{text}', pdf_rect стал невалидным после проверки пересечений ({pdf_rect}).")

        except (ValueError, TypeError, KeyError) as e_row:
             logger_ocr.warning(f"Ошибка обработки строки кандидата OCR: {e_row}. Строка: {row.to_dict()}", exc_info=False)
        except Exception as e_cand:
             logger_ocr.error(f"Неожиданная ошибка при проверке кандидата OCR '{row.get('text', 'N/A')}': {e_cand}", exc_info=True)

    logger_ocr.info(f"Найдено {len(candidates)} итоговых OCR кандидатов для подсветки (после всех проверок).")
    return candidates

# --- END OF FILE ocr_service.py ---