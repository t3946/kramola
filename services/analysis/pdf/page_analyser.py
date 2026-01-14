import logging
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pymupdf

from services.analysis.pdf.char import Char
from services.analysis.pdf.pua_map import PuaMap

logger = logging.getLogger(__name__)


class PageAnalyser:
    """
    Класс для сбора и нормализации текста из PDF.
    Собирает символы посимвольно и предоставляет методы для нормализации.
    """

    def __init__(self, page: 'pymupdf.Page', pua_map: PuaMap) -> None:
        """
        Args:
            page: Страница PDF документа
            pua_map: Экземпляр PuaMap для преобразования символов
        """
        self.page: 'pymupdf.Page' = page
        self.pua_map: PuaMap = pua_map
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

        self._chars.append(char)
        self._last_y = current_y
        self._is_first_char = False

    def get_chars(self) -> List[Char]:
        return self._chars

    def collect(self) -> None:
        """
        Собирает символы из страницы PDF.
        """
        raw_dict = self.page.get_text("rawdict")

        for block in raw_dict['blocks']:
            if 'lines' not in block:
                continue

            for i, line in enumerate(block['lines']):
                has_wrap = False

                # [start] process line text
                for span in line['spans']:
                    font_name = span.get('font', '')

                    for j, char in enumerate(span['chars']):
                        char_str = self.pua_map.char_to_str(char, font_name, self.page)
                        bbox = char.get('bbox', [])

                        # if line ends up with '-' then it word wrap suppose
                        if char_str == '-' and j == len(span['chars']) - 1:
                            has_wrap = True
                            continue

                        # add char into collected text
                        char_obj = Char(char=char_str, bbox=bbox)
                        self.add_char(char_obj)
                # [end]

                # [start] add space as lines separator
                is_last_line = i == len(block['lines']) - 1

                if not has_wrap and not is_last_line and self._chars:
                    last_char = self._chars[-1]

                    if last_char.char != ' ':
                        self.add_char(Char(' '))
                # [end]

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
