# --- START OF FILE services/common_docx.py ---

import logging
import copy
from docx.shared import RGBColor, Pt # Импортируем необходимые типы
import re

from . import pymorphy_service

PYMORPHY_AVAILABLE = True


TOKENIZE_PATTERN_UNIVERSAL = re.compile(r"(\w+)|([^\w\s]+)|(\s+)", re.UNICODE)
# --- Настройка логгера ---
# Используем свой логгер для этого модуля, чтобы не смешивать логи
logger_cd = logging.getLogger(__name__)

# --- Общие функции для работы с форматированием DOCX ---


def _safe_copy_paragraph_format(source_pf, target_pf):
    """
    Безопасно копирует основные атрибуты форматирования параграфа.
    (Скопировано из footnotes_service.py / highlight_service.py)
    """
    if not source_pf or not target_pf: return
    # Атрибуты, которые безопасно копировать
    attrs_to_copy = [
        'alignment', 'first_line_indent', 'keep_together', 'keep_with_next',
        'left_indent', 'line_spacing', 'line_spacing_rule', 'page_break_before',
        'right_indent', 'space_after', 'space_before', 'widow_control'
    ]
    for attr in attrs_to_copy:
        try:
            val = getattr(source_pf, attr, None)
            # Копируем только если значение не None, чтобы не перезаписать умолчания None'ом
            if val is not None:
                setattr(target_pf, attr, val)
        except (AttributeError, ValueError, TypeError) as e:
            # Используем логгер этого модуля
            logger_cd.warning(f"Предупреждение при копировании формата параграфа '{attr}': {e}", exc_info=False)

def _apply_run_style(source_run, target_run, copy_highlight=False):
    """
    Применяет стиль и форматирование от source_run к target_run.
    (Скопировано из footnotes_service.py / highlight_service.py и адаптировано)
    copy_highlight: Если True, копирует цвет подсветки из ИСХОДНОГО рана.
    """
    if not source_run or not target_run: return

    try:
        # 1. Копирование стиля символов (Character Style)
        if hasattr(source_run, 'style') and source_run.style:
             if hasattr(source_run.style, 'name') and source_run.style.name:
                 try:
                     style_name = source_run.style.name
                     # Проверяем наличие стиля в целевом документе перед применением
                     if style_name in target_run.part.document.styles:
                          target_run.style = target_run.part.document.styles[style_name]
                 except Exception as e:
                     # Используем логгер этого модуля
                     logger_cd.warning(f"Не удалось присвоить стиль run '{getattr(source_run.style,'name','N/A')}': {e}")

        # 2. Копирование прямого форматирования (логические атрибуты)
        bool_attrs = [
            'bold', 'italic', 'underline', 'small_caps', 'all_caps', 'strike', 'double_strike',
            'outline', 'shadow', 'imprint', 'emboss', 'spec_vanish', 'no_proof', 'snap_to_grid',
            'rtl', 'cs_bold', 'cs_italic', 'web_hidden'
        ]
        for attr in bool_attrs:
            try:
                val = getattr(source_run, attr, None)
                if val is not None: setattr(target_run, attr, val)
            except (AttributeError, ValueError, TypeError):
                # Игнорируем ожидаемые ошибки атрибутов
                pass
            except Exception as e_bool: # Ловим прочие для отладки
                logger_cd.warning(f"Неожиданная ошибка при копировании bool атрибута '{attr}': {e_bool}")


        # 3. Копирование атрибутов шрифта (font)
        if hasattr(source_run, 'font') and source_run.font:
            s_font = source_run.font
            t_font = target_run.font
            # Основные атрибуты шрифта
            font_attrs = ['name', 'size', 'color', 'underline', 'highlight_color']

            for attr in font_attrs:
                try:
                    val = getattr(s_font, attr, None)
                    if val is not None:
                        # Обработка цвета (копируем RGB если возможно)
                        if attr == 'color':
                             if hasattr(val, 'rgb') and isinstance(val.rgb, RGBColor):
                                 # Используем deepcopy для RGBColor на всякий случай
                                 try: t_font.color.rgb = copy.deepcopy(val.rgb)
                                 except Exception as e_assign_rgb: logger_cd.warning(f"Не удалось присвоить RGB цвет: {e_assign_rgb}")
                             # Можно добавить обработку theme_color, если необходимо
                        # Обработка размера (копируем Pt если возможно)
                        elif attr == 'size':
                            if hasattr(val, 'pt') and val.pt is not None:
                                try:
                                    pt_size = int(val.pt)
                                    if pt_size > 0: t_font.size = Pt(pt_size)
                                except (ValueError, TypeError): pass # Игнорируем некорректные размеры
                        # Обработка подчеркивания
                        elif attr == 'underline':
                             t_font.underline = val # Копируем как есть (может быть True, False, Enum)
                        # Обработка имени шрифта
                        elif attr == 'name' and val: # Убедимся что имя не пустое
                             t_font.name = val
                        # Обработка цвета подсветки (только если copy_highlight=True)
                        elif attr == 'highlight_color' and copy_highlight:
                             t_font.highlight_color = val # Копируем как есть (обычно Enum WD_COLOR_INDEX или None)
                except Exception as e:
                    # Используем логгер этого модуля
                    logger_cd.warning(f"Ошибка копирования атрибута шрифта '{attr}': {e}", exc_info=False)

            # Копирование прочих атрибутов шрифта
            misc_font_attrs = ['kerning', 'subscript', 'superscript']
            for attr in misc_font_attrs:
                 try:
                     val = getattr(s_font, attr, None)
                     if val is not None: setattr(t_font, attr, val)
                 except (AttributeError, ValueError, TypeError): pass
                 except Exception as e_misc:
                     logger_cd.warning(f"Неожиданная ошибка при копировании misc атрибута шрифта '{attr}': {e_misc}")

    except Exception as e:
        # Используем логгер этого модуля
        logger_cd.error(f"Критическая ошибка в _apply_run_style: {e}", exc_info=True)

def tokenize_paragraph_universal(paragraph):
    """
    Универсальная токенизация параграфа DOCX.

    Возвращает список словарей, каждый из которых содержит:
        - 'text': str - сам текст токена
        - 'start': int - начальная позиция
        - 'end': int - конечная позиция
        - 'type': str - тип токена ('word', 'punct', 'space')
        - 'lemma': str | None - лемма (только для type='word')
        - 'stem': str | None - стемм (только для type='word')
    """
    tokens = []
    full_text = ""
    try:
        # Получаем текст параграфа безопасно
        full_text = paragraph.text if paragraph else ""
        if not full_text:
            return tokens # Возвращаем пустой список для пустого параграфа

        current_pos = 0
        for match in TOKENIZE_PATTERN_UNIVERSAL.finditer(full_text):
            start, end = match.span()
            text = match.group(0)

            # Обработка пропущенного текста (если паттерн что-то упустил)
            if start > current_pos:
                missed_text = full_text[current_pos:start]
                # Считаем пропущенный текст "пунктуацией" для простоты
                tokens.append({
                    'text': missed_text, 'start': current_pos, 'end': start,
                    'type': 'punct', 'lemma': None, 'stem': None
                })
                logger_cd.warning(f"Обнаружен пропущенный текст при токенизации: '{missed_text}'")

            token_type = 'punct' # Default
            lemma = None
            stem = None

            if match.group(1): # Группа для слов (\w+)
                token_type = 'word'
                # Получаем лемму и стемм только для слов
                word_lower = text.lower()

                if PYMORPHY_AVAILABLE:
                    try:
                        lemma = pymorphy_service._get_lemma(word_lower)
                    except Exception as e_lemma:
                        logger_cd.error(f"Ошибка получения леммы для '{text}': {e_lemma}", exc_info=False)
                    try:
                        stem = pymorphy_service._get_stem(word_lower)
                    except Exception as e_stem:
                        logger_cd.error(f"Ошибка получения стеммы для '{text}': {e_stem}", exc_info=False)
                else:
                    # Используем заглушки, если pymorphy_service не импортировался
                    lemma = pymorphy_service._get_lemma(word_lower)
                    stem = pymorphy_service._get_stem(word_lower)

            elif match.group(3): # Группа для пробелов (\s+)
                token_type = 'space'
            # Группа 2 ([^\w\s]+) остается 'punct' по умолчанию

            tokens.append({
                'text': text, 'start': start, 'end': end,
                'type': token_type, 'lemma': lemma, 'stem': stem
            })
            current_pos = end

        # Обработка текста после последнего совпадения
        if current_pos < len(full_text):
            remaining_text = full_text[current_pos:]
            tokens.append({
                'text': remaining_text, 'start': current_pos, 'end': len(full_text),
                'type': 'punct', 'lemma': None, 'stem': None
            })
            logger_cd.warning(f"Обнаружен остаточный текст при токенизации: '{remaining_text}'")

    except Exception as e:
        logger_cd.error(f"Критическая ошибка в tokenize_paragraph_universal: {e}", exc_info=True)
        # Возвращаем пустой список в случае ошибки
        return []

    return tokens


# --- END OF FILE services/common_docx.py ---   