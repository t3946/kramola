import logging
import io
import pymupdf
from PIL import Image
from typing import Optional, Dict, Tuple
from services.ocr_service import setup_tesseract_path, ocr_single_character

setup_tesseract_path()

logger = logging.getLogger(__name__)


class PuaMap:
    """
    Класс для маппинга PUA (Private Use Area) символов Unicode.
    Хранит маппинг <шрифт>+<код символа> -> распознанный символ.
    """

    def __init__(self) -> None:
        self._mapping: Dict[Tuple[str, int], str] = {}

    @staticmethod
    def _is_pua_char(char: str) -> bool:
        """
        Check if character is in Private Use Area (PUA).
        """
        if not char:
            return False

        code = ord(char[0])

        return 0xE000 <= code <= 0xF8FF

    def char_to_str(self, char: Dict, font_name: str, page: pymupdf.Page) -> str:
        """
        Преобразует символ из PDF в строку.
        Если символ PUA и не найден в кэше - выполняет OCR и сохраняет результат.

        Args:
            char: Словарь символа из PDF с ключами 'c' (символ) и 'bbox' (координаты)
            font_name: Имя шрифта
            page: Страница PDF для выполнения OCR

        Returns:
            Распознанный символ или исходный символ, если не PUA
        """
        char_value = char.get('c', '')

        # common char
        if not self._is_pua_char(char_value):
            return char_value

        # [start] get char from maps
        char_code = ord(char_value[0])
        cache_key = (font_name, char_code)

        if cache_key in self._mapping:
            return self._mapping[cache_key]
        # [end]

        # [start] try ocr to get unknown char
        bbox = char.get('bbox', [])

        if len(bbox) != 4:
            return char_value

        x0, y0, x1, y1 = bbox
        char_rect = pymupdf.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(clip=char_rect, matrix=pymupdf.Matrix(3, 3))

        img_bytes = pix.tobytes("png")
        img_pil = Image.open(io.BytesIO(img_bytes))

        ocr_char = ocr_single_character(img_pil, languages='rus')

        if ocr_char:
            self._mapping[cache_key] = ocr_char

            return ocr_char

        self._mapping[cache_key] = char_value
        # [end]

        return char_value
