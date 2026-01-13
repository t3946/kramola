from typing import List


class Char:
    """
    Класс для представления символа из PDF с его координатами.
    """

    def __init__(self, char: str, bbox: List[float]) -> None:
        """
        Args:
            char: Расшифрованный символ
            bbox: Координаты символа [x0, y0, x1, y1]
        """
        self.char: str = char
        self.bbox: List[float] = bbox

