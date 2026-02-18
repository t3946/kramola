import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

import pymupdf

from models.inagents import AgentType
from services.analysis import AnalysisMatch
from services.enum.predefined_list import ESearchSourceAnnotTitle
from services.fulltext_search import Phrase
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch

if TYPE_CHECKING:
    pass

from models import Inagent
from services.analysis.pdf.char import Char
from services.analysis.pdf.pua_map import PuaMap

logger = logging.getLogger(__name__)

WRAP_HYPHEN_CHARS: tuple[str, ...] = ('-', '\u00AD')


class PageAnalyser:
    """
    Класс для сбора и нормализации текста из PDF.
    Собирает символы посимвольно и предоставляет методы для нормализации.
    """

    def __init__(self, page: 'pymupdf.Page', pua_map: PuaMap, highlight_color: Tuple[float, float, float]) -> None:
        """
        Args:
            page: Страница PDF документа
            pua_map: Экземпляр PuaMap для преобразования символов
        """
        self.page: 'pymupdf.Page' = page
        self.pua_map: PuaMap = pua_map
        self.highlight_color: Tuple[float, float, float] = highlight_color
        self._chars: List[Char] = []
        self._wrap_indices: List[int] = []
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
                for span_idx, span in enumerate(line['spans']):
                    is_last_span = span_idx == len(line['spans']) - 1
                    font_name = span.get('font', '')

                    for j, char in enumerate(span['chars']):
                        char_str = self.pua_map.char_to_str(char, font_name, self.page)
                        bbox = char.get('bbox', [])

                        # if line ends with a hyphen then it is a word wrap
                        is_last_char_in_span = j == len(span['chars']) - 1

                        if char_str in WRAP_HYPHEN_CHARS and is_last_span and is_last_char_in_span:
                            has_wrap = True

                            if self._chars:
                                self._wrap_indices.append(len(self._chars) - 1)

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

    def to_text(self) -> str:
        """
        Выполняет простую склейку всех символов в готовый текст.

        Returns:
            Склеенный текст из всех символов
        """
        return ''.join(char_obj.char for char_obj in self._chars)

    def normalize(self) -> str:
        return self.to_text()

    def highlight_range(self, start: int, end: int, match: Optional[AnalysisMatch] = None) -> None:
        """
        Выделяет текст на странице PDF для заданного диапазона символов.

        Args:
            start: Начальный индекс символа (включительно)
            end: Конечный индекс символа (включительно)
            match: match details
        """
        if not self._chars:
            return

        # [start] validate and clamp range
        start = max(0, start)
        end = min(len(self._chars) - 1, end)

        if start > end:
            return
        # [end]

        # [start] split range by word wraps
        wrap_index = next((i for i in self._wrap_indices if start <= i < end), None)

        if wrap_index is not None:
            self.highlight_range(start, wrap_index, match)
            self.highlight_range(wrap_index + 1, end, None)

            return
        # [end]

        # [start] collect valid bboxes from range
        valid_chars: List[Char] = []

        for i in range(start, end + 1):
            char = self._chars[i]

            if char.bbox and len(char.bbox) >= 4:
                valid_chars.append(char)
        # [end]

        if not valid_chars:
            return

        # [start] calculate bounding rect
        x0 = min(char.bbox[0] for char in valid_chars)
        y0 = min(char.bbox[1] for char in valid_chars)
        x1 = max(char.bbox[2] for char in valid_chars)
        y1 = max(char.bbox[3] for char in valid_chars)
        # [end]

        rect = pymupdf.Rect(x0, y0, x1, y1)
        annot: pymupdf.Annot = self.page.add_highlight_annot(rect)
        annot.set_colors(stroke=self.highlight_color)

        #[start] annot content
        if isinstance(match.search_match, FTSTextMatch):
            phrase: Phrase = match.search_match.search_phrase
            content = phrase.phrase_original if phrase.phrase_original else phrase.phrase
            title = getattr(ESearchSourceAnnotTitle, phrase.source.name).value

            if phrase.source.name == ESearchSourceAnnotTitle.LIST_INAGENTS.name:
                content = ''
                inagents: list[Inagent] = Inagent.get_by_term(phrase.phrase)

                if inagents[0]:
                    inagent = inagents[0]

                    if inagent.agent_type == AgentType.FIZ.value:
                        content = "\n".join([
                            "Иноагент",
                            f"{inagent.full_name}",
                            f"Дата рождения: {inagent.birth_date}",
                            "",
                            "Деятельность: нет",
                            f"В реестре с: {inagent.include_minjust_date}",
                            "",
                            f"Основание: {inagent.include_reason}"
                        ])
                    else:
                        content = "\n".join([
                            "Иноагент",
                            f"{inagent.full_name}",
                            "",
                            "Деятельность: нет",
                            f"В реестре с: {inagent.include_minjust_date}",
                            "",
                            f"Основание: {inagent.include_reason}"
                        ])

            annot.set_info({
                "title": title,
                "content": content,
            })
        elif isinstance(match.search_match, FTSRegexMatch):
            annot.set_info({
                "title": "Шаблон",
                "content": f"«{match.search_match.regex_info.pattern_name}»",
            })
        #[end]

        annot.update()
