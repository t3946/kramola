# utils.py
import logging
import os

def load_lines_from_txt(filepath):
    """Загружает строки из текстового файла, удаляя пустые строки и пробелы по краям."""
    lines = []
    try:
        # Используем utf-8-sig для обработки BOM (Byte Order Mark), если он есть
        # Читаем файл целиком для лучшей производительности
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            lines = [line.strip() for line in content.splitlines() if line.strip()]
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