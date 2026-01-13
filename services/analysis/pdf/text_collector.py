import logging
from typing import List

logger = logging.getLogger(__name__)


class TextCollector:
    """
    Класс для сбора и нормализации текста из PDF.
    Собирает символы посимвольно и предоставляет методы для нормализации.
    """

    def __init__(self) -> None:
        self._chars: List[str] = []

    def add_char(self, char: str) -> None:
        """
        Добавляет символ в коллекцию.

        Args:
            char: Символ для добавления
        """
        self._chars.append(char)

    def _to_text(self) -> str:
        """
        Выполняет простую склейку всех символов в готовый текст.

        Returns:
            Склеенный текст из всех символов
        """
        return ''.join(self._chars)

    def _solve_wraps(self) -> None:
        """
        Фильтр для решения переносов строк.
        """
        pass

    def normalize(self) -> str:
        """
        Запускает приватные методы-фильтры для нормализации текста.

        Returns:
            Нормализованный текст
        """
        self._solve_wraps()

        return self._to_text()

