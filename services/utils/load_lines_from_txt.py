import logging


def load_lines_from_txt(filepath: str) -> list[str]:
    """Загружает строки из текстового файла, удаляя пустые строки и пробелы по краям."""
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            lines = [line.strip() for line in content.splitlines() if line.strip()]
        logging.debug(f"Успешно загружено {len(lines)} строк из файла: {filepath}")
    except FileNotFoundError:
        logging.error(f"Файл не найден: {filepath}")
        return []
    except Exception as e:
        logging.error(f"Ошибка чтения файла {filepath}: {e}", exc_info=True)
        return []
    return lines


