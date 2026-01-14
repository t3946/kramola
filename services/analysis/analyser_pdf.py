import os
import itertools
import re
import pymupdf
import pandas as pd

from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from collections import defaultdict, Counter
from services.analysis import AnalysisData
from services.analysis.analyser import Analyser
from services.fulltext_search.token import Token, TokenType
from services.fulltext_search.dictionary import TokenDictionary
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.fulltext_search import FulltextSearch, STOP_WORDS_RU, STOP_WORDS_EN, SearchStrategy, Match
from services.pymorphy_service import _get_lemma, _get_stem, CYRILLIC_PATTERN
from services.ocr_service import ocr_page, OCR_LANGUAGES, OCR_DPI
from services.utils.timeit import timeit
from services.analysis.pdf.pua_map import PuaMap
from services.analysis.pdf.page_analyser import PageAnalyser

# if TYPE_CHECKING:
#     from services.progress.pdf.combined_progress import CombinedProgress

HIGHLIGHT_COLOR_PDF = (0.0, 1.0, 0.0)
WORDS_EXTRACT_PATTERN = re.compile(r'[a-zA-Zа-яА-ЯёЁ]+', re.UNICODE)
PUNCT_STRIP_PATTERN = re.compile(r"^[^\w\s]+|[^\w\s]+$", re.UNICODE)
MIN_OCR_CONFIDENCE_HIGHLIGHT = 40
HYPHEN_CHARS = ('-', '\u00AD')
MAX_LINE_JUMP_MERGE = 150
HORIZONTAL_INDENT_THRESHOLD = 200
MIN_CONF_FOR_MERGE = 5
USE_STEM_FALLBACK = True


class AnalyserPdf(Analyser):
    document: pymupdf.Document
    source_path: str
    # _progress: Optional['CombinedProgress']

    def __init__(self, source_path: str):
        super().__init__()
        self.source_path = source_path
        self.document = None
        self._progress = None

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None) -> dict:
        self.word_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.phrase_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.document = pymupdf.open(self.source_path)

        pages_to_process = len(self.document)

        # [start] Collect pages
        pua_map = PuaMap()
        pages = []

        for page_num in range(pages_to_process):
            page = self.document.load_page(page_num)
            page_analyser = PageAnalyser(page=page, pua_map=pua_map)
            page_analyser.collect()
            pages.append(page_analyser)
        # [end]

        # [start] tokenize document and run search
        whole_document_text = ''

        for page_analyser in pages:
            whole_document_text += page_analyser.normalize() + ' '

        all_tokens: List[Token] = FulltextSearch.tokenize_text(whole_document_text)
        phrases_list = list(self.analyse_data.phrases.values())
        search_phrases_for_search: List[Tuple[str, List[Token]]] = [
            (phrase.phrase, phrase.tokens) for phrase in phrases_list
        ]
        fulltext_search = FulltextSearch(all_tokens)
        phrase_results = fulltext_search.search_all(search_phrases_for_search, SearchStrategy.FUZZY_WORDS_PUNCT)
        
        matches = self._convert_phrase_results_to_matches(phrase_results, phrases_list)

        for match in matches:
            self._update_match_statistics(match, all_tokens)
        # [end]

        return self._get_stats_result()

    def save(self, output_path: str) -> None:
        if self.document is None:
            return

        total_highlight_actions = sum(d['count'] for d in self.word_stats.values()) + sum(
            d['count'] for d in self.phrase_stats.values()
        )

        if total_highlight_actions > 0:
            try:
                self.document.save(output_path, garbage=4, deflate=True, clean=True)
            except Exception:
                if self.document:
                    self.document.close()
                return
        else:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

        if self.document:
            try:
                self.document.close()
            except Exception:
                pass
