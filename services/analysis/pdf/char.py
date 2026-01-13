import re
from typing import List

class Char:
    """
    Класс для представления символа из PDF с его координатами.
    """

    def __init__(self, char: str, bbox: List[float] = None) -> None:
        """
        Args:
            char: Расшифрованный символ
            bbox: Координаты символа [x0, y0, x1, y1]
        """
        normalized_char = self._normalize_space(char)
        self.char: str = normalized_char
        self.bbox: List[float] = bbox

    @staticmethod
    def _normalize_space(char: str) -> str:
        """
        Нормализует все пробельные символы (NBSP и другие) в обычный пробел.

        Args:
            char: Исходный символ

        Returns:
            Символ с нормализованными пробелами
        """
        if not char:
            return char

        if char == ' ':
            return ' '

        return char

