import logging
from typing import List, Optional
from services.analysis.pdf.char import Char

logger = logging.getLogger(__name__)


class TextCollector:
    """
    Класс для сбора и нормализации текста из PDF.
    Собирает символы посимвольно и предоставляет методы для нормализации.
    """

    def __init__(self) -> None:
        self._chars: List[Char] = []
        self._last_y: Optional[float] = None
        self._is_first_char: bool = True

    def add_char(self, char: Char) -> None:
        """
        Добавляет символ в коллекцию.
        Добавляет пробел между строками, если обнаружен переход на новую строку.

        Args:
            char: Объект Char для добавления
        """
        if not char.bbox or len(char.bbox) < 4:
            self._chars.append(char)
            return

        current_y = char.bbox[1]
        Y_TOLERANCE = 5.0

        if not self._is_first_char and self._last_y is not None:
            y_diff = abs(current_y - self._last_y)

            if y_diff > Y_TOLERANCE:
                if self._chars and self._chars[-1].char != ' ' and char.char != ' ':
                    space_char = Char(char=' ', bbox=[])
                    self._chars.append(space_char)

        self._chars.append(char)
        self._last_y = current_y
        self._is_first_char = False

    def _to_text(self) -> str:
        """
        Выполняет простую склейку всех символов в готовый текст.

        Returns:
            Склеенный текст из всех символов
        """
        return ''.join(char_obj.char for char_obj in self._chars)

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

