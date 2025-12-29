import re
import logging
import fitz
from typing import List, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

HAS_ANY_LETTER_PATTERN = re.compile(r'[a-zA-Zа-яА-ЯёЁ]')


def is_predominantly_non_alphabetic(text_segment: str, min_letter_ratio: float = 0.5) -> bool:
    if not text_segment or not isinstance(text_segment, str):
        return True

    stripped_text = text_segment.strip()

    if not stripped_text:
        return True

    letters_found = HAS_ANY_LETTER_PATTERN.findall(stripped_text)
    num_letters = len(letters_found)
    total_len = len(stripped_text)

    if total_len == 0:
        return True

    letter_ratio = num_letters / total_len

    if letter_ratio < min_letter_ratio:
        logger.debug(f"Marked as garbage: '{text_segment}', Ratio={letter_ratio:.2f} < {min_letter_ratio}")
        return True

    return False


def extract_logical_words_from_block(block_words: List, block_rect: fitz.Rect) -> List[Dict[str, any]]:
    """
    Склеивает переносы ТОЛЬКО ПО ДЕФИСУ.
    Возвращает 'rects' как список кортежей координат [(x0,y0,x1,y1), ...].
    """
    logical_words_in_block = []
    VERTICAL_TOLERANCE = 5.0
    MIN_LINE_JUMP = 8.0
    MIN_WORD_PART_LEN = 2

    i = 0
    num_words = len(block_words)

    while i < num_words:
        current_word_info = block_words[i]

        try:
            x0, y0, x1, y1, current_text_raw, _, _, _, _ = current_word_info
        except ValueError:
            logger.error(f"Ошибка распаковки word_info: {current_word_info}", exc_info=False)
            i += 1
            continue

        current_text = current_text_raw.strip()

        if not current_text or x0 >= x1 or y0 >= y1:
            i += 1
            continue

        current_coords = (x0, y0, x1, y1)

        potential_hyphen_removed = False
        cleaned_current_text = current_text
        hyphen_chars = '-\u2010\u2013\u2014\u00AD'

        if current_text.endswith(tuple(hyphen_chars)):
            temp_cleaned = current_text.rstrip(hyphen_chars)

            if temp_cleaned:
                cleaned_current_text = temp_cleaned
                potential_hyphen_removed = True

        found_merge = False

        if i + 1 < num_words:
            next_word_info = block_words[i+1]

            try:
                nx0, ny0, nx1, ny1, next_text_raw, _, _, _, _ = next_word_info
            except ValueError:
                logger.error(f"Ошибка распаковки next_word_info: {next_word_info}", exc_info=False)
                logical_words_in_block.append({'text': cleaned_current_text, 'rects': [current_coords]})
                i += 1
                continue

            next_text = next_text_raw.strip()

            if next_text and nx0 < nx1 and ny0 < ny1:
                is_vertically_close = abs(y0 - ny0) < VERTICAL_TOLERANCE
                is_next_line_below = ny0 > y0 + MIN_LINE_JUMP
                is_long_enough = len(cleaned_current_text) >= MIN_WORD_PART_LEN and len(next_text) >= MIN_WORD_PART_LEN
                condition1_hyphen = potential_hyphen_removed and is_next_line_below and is_long_enough

                if not is_vertically_close and condition1_hyphen:
                    next_coords = (nx0, ny0, nx1, ny1)
                    merged_text = cleaned_current_text + next_text
                    logical_words_in_block.append({'text': merged_text, 'rects': [current_coords, next_coords]})
                    logger.info(f"    Блок {block_rect}: >>> СКЛЕЕНО (Дефис): '{current_text_raw}' + '{next_text_raw}' -> '{merged_text}'")
                    i += 2
                    found_merge = True

        if not found_merge:
            logical_words_in_block.append({'text': cleaned_current_text, 'rects': [current_coords]})
            i += 1

    return logical_words_in_block


def extract_all_logical_words_from_pdf(pdf_path: str) -> Optional[List[List[Dict[str, any]]]]:
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
    logger.info(f"Начало извлечения лог. слов из PDF (с проверкой коорд. и фильтрацией мусора): {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
        logger.debug(f"Открыт PDF, страниц: {len(doc)}")
        all_words_data_raw = []
        all_blocks_data_raw = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            words_on_page = page.get_text("words", sort=True)
            blocks_on_page = page.get_text("blocks", sort=True)

            for w in words_on_page:
                all_words_data_raw.append(list(w) + [page_num])

            for b in blocks_on_page:
                all_blocks_data_raw.append(list(b) + [page_num])

        for page_num in range(len(doc)):
            logger.debug(f"--- Обработка страницы {page_num + 1} ---")
            logical_words_on_page = []
            current_page_blocks = [b for b in all_blocks_data_raw if b[7] == page_num]
            current_page_words_raw = [w for w in all_words_data_raw if w[8] == page_num]

            for block_data in current_page_blocks:
                block_type = block_data[6]

                if block_type != 0:
                    continue

                bx0, by0, bx1, by1, _, block_no, _, _ = block_data

                if bx0 >= bx1 or by0 >= by1:
                    logger.warning(f"Пропуск блока {block_no} на стр. {page_num+1} из-за невалидных координат: ({bx0},{by0},{bx1},{by1})")
                    continue

                try:
                    block_rect_for_logging = fitz.Rect(bx0, by0, bx1, by1)
                    logger.debug(f"  Обработка блока {block_no} (Тип {block_type}) с Rect: {block_rect_for_logging}")
                except Exception as e_rect_block:
                    logger.warning(f"  Ошибка создания Rect для блока {block_no} на стр. {page_num+1}: {e_rect_block}. Пропуск блока.")
                    continue

                epsilon = 1.0
                words_in_this_block_raw = [
                    w for w in current_page_words_raw
                    if w[0] >= bx0 - epsilon and w[1] >= by0 - epsilon and
                       w[2] <= bx1 + epsilon and w[3] <= by1 + epsilon
                ]

                words_in_this_block_raw.sort(key=lambda w: (w[6], w[7]))

                logger.debug(f"    Найдено {len(words_in_this_block_raw)} сырых слов в блоке {block_no}.")

                if words_in_this_block_raw:
                    logical_words_from_block_extraction = extract_logical_words_from_block(words_in_this_block_raw, block_rect_for_logging)

                    filtered_logical_words_for_block = []

                    for logical_word_dict in logical_words_from_block_extraction:
                        text_to_check = logical_word_dict.get('text', '')

                        if not is_predominantly_non_alphabetic(text_to_check):
                            filtered_logical_words_for_block.append(logical_word_dict)
                        else:
                            logger.debug(f"    Отфильтровано логическое слово из блока {block_no} (стр. {page_num+1}) из-за содержимого: '{text_to_check}'")

                    if filtered_logical_words_for_block:
                        logical_words_on_page.extend(filtered_logical_words_for_block)
                        logger.debug(f"    Добавлено {len(filtered_logical_words_for_block)} (после фильтрации) лог. слов из блока {block_no}.")

            all_pages_logical_words.append(logical_words_on_page)
            logger.debug(f"--- Страница {page_num + 1}: Собрано {len(logical_words_on_page)} логических слов (после фильтрации) ---")

        logger.info(f"Завершено извлечение логических слов из PDF (с фильтрацией).")
        return all_pages_logical_words

    except Exception as e_general:
        logger.error(f"Критическая ошибка при извлечении лог. слов из PDF '{pdf_path}': {e_general}", exc_info=True)
        return None

    finally:
        if doc:
            try:
                doc.close()
                logger.debug(f"PDF документ {pdf_path} закрыт.")
            except Exception as e_close:
                logger.warning(f"Не удалось корректно закрыть PDF документ {pdf_path}: {e_close}")

