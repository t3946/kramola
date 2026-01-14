import os
import itertools
import re
import pymupdf
import pandas as pd

from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from collections import defaultdict, Counter
from services.analysis import AnalysisData
from services.fulltext_search.token import Token, TokenType
from services.fulltext_search.dictionary import TokenDictionary
from services.fulltext_search.phrase import Phrase
from services.fulltext_search.fulltext_search import FulltextSearch, STOP_WORDS_RU, STOP_WORDS_EN
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


class AnalyserPdf:
    document: pymupdf.Document
    source_path: str
    analyse_data: AnalysisData
    word_stats: defaultdict
    phrase_stats: defaultdict
    _global_document_dictionary: Optional[TokenDictionary]
    _search_phrases: List[Phrase]

    # _progress: Optional['CombinedProgress']

    def __init__(self, source_path: str):
        self.source_path = source_path
        self.document = None
        self.word_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.phrase_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self._global_document_dictionary = None
        self._search_phrases = []
        self._progress = None

    def set_analyse_data(self, analyse_data: AnalysisData) -> None:
        self.analyse_data = analyse_data

    def __filter_phrases_by_dictionary(
            self,
            search_phrases: List[Phrase],
            dictionary: TokenDictionary
    ) -> List[Phrase]:
        """Filter phrases: exclude those where at least one word is missing in dictionary."""
        filtered_phrases: List[Phrase] = []

        for phrase in search_phrases:
            search_words = [t for t in phrase.tokens if t.type == TokenType.WORD]

            if len(search_words) == 0:
                continue

            filtered_words = dictionary.filter_tokens(search_words)

            if len(filtered_words) == len(search_words):
                filtered_phrases.append(phrase)

        return filtered_phrases

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None) -> dict:
        self.word_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.phrase_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.document = pymupdf.open(self.source_path)

        #todo: debug only
        pages_to_process = 1#len(self.document)

        # [start] Collect pages
        pua_map = PuaMap()
        pages = []

        for page_num in range(pages_to_process):
            page = self.document.load_page(page_num)
            page_analyser = PageAnalyser(page=page, pua_map=pua_map)
            page_analyser.collect()
            pages.append(page_analyser)
        # [end]

        # [start] build global dictionary and filter search phrases by it
        whole_document_text = ''

        for page_analyser in pages:
            whole_document_text += page_analyser.normalize() + ' '

        all_tokens: List[Token] = FulltextSearch.tokenize_text(whole_document_text)
        self._global_document_dictionary = TokenDictionary(all_tokens)
        phrases_list = list(self.analyse_data.phrases.values())
        self._search_phrases = self.__filter_phrases_by_dictionary(
            phrases_list,
            self._global_document_dictionary
        )
        # [end]

        # [start] stats forming
        total_matches_combined = sum(d['count'] for d in self.word_stats.values()) + sum(
            d['count'] for d in self.phrase_stats.values()
        )

        final_ws = {
            l: {
                'count': d['count'],
                'forms': dict(d['forms'])
            } for l, d in self.word_stats.items()
        }
        final_ps = {
            phrase_lemma_str: {
                'count': d['count'],
                'forms': dict(d['forms'])
            } for phrase_lemma_str, d in self.phrase_stats.items()
        }
        # [end]

        return {'word_stats': final_ws, 'phrase_stats': final_ps, 'total_matches': total_matches_combined}

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
