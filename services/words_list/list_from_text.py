from pathlib import Path
from typing import List, Optional, Union

import json
from flask import current_app

from services.document_service import extract_lines_from_docx
from services.fulltext_search.phrase import Phrase
from services.utils.load_lines_from_txt import load_lines_from_txt
from services.words_list.list_user_custom import ListUserCustom


class ListFromText(ListUserCustom):
    """Phrases passed as text (lines split by newline)."""

    _redis_key: str = "search_terms_json"
    _redis_name: str
    _task_id: str

    def __init__(self, task_id: str) -> None:
        self._task_id = task_id
        self._redis_name = f"task:{task_id}"
        super().__init__()

    def load(self) -> List[Phrase]:
        redis_client = getattr(current_app, 'redis_client_tasks', None)
        lines_json = redis_client.hget(self._redis_name, self._redis_key)

        if lines_json is None:
            return []

        lines = json.loads(lines_json)
        phrases: List[Phrase] = []

        for text in lines:
            phrases.append(Phrase(text, source_list=self))

        return phrases

    def _write_lines_to_redis(self, lines: List[str]) -> None:
        redis_client = getattr(current_app, 'redis_client_tasks', None)
        redis_client.hset(self._redis_name, self._redis_key, json.dumps(lines))
        redis_client.expire(self._redis_name, int(current_app.config["REDIS_TASK_TTL"]))

    def save_from_text(self, lines: List[str]) -> None:
        self._write_lines_to_redis(lines)

    def save_from_file(self, path: Optional[Union[str, Path]]) -> None:
        path_str = str(path)
        ext = Path(path_str).suffix.lower()

        if ext == '.docx':
            lines = extract_lines_from_docx(path_str)
        else:
            lines = load_lines_from_txt(path_str)

        self._write_lines_to_redis(lines)
