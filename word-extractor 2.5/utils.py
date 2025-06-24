# utils.py
import logging
import os

def load_lines_from_txt(filepath):
    """Загружает строки из текстового файла, удаляя пустые строки и пробелы по краям."""
    lines = []
    try:
        # Используем utf-8-sig для обработки BOM (Byte Order Mark), если он есть
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line: # Добавляем только непустые строки
                    lines.append(stripped_line)
        logging.debug(f"Успешно загружено {len(lines)} строк из файла: {filepath}")
    except FileNotFoundError:
        logging.error(f"Файл не найден: {filepath}")
        # Возвращаем пустой список, чтобы не прерывать работу, но логируем ошибку
        return []
    except Exception as e:
        logging.error(f"Ошибка чтения файла {filepath}: {e}", exc_info=True)
        # Возвращаем пустой список при других ошибках
        return []
    return lines