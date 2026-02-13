import re
import pymupdf

from typing import List, Optional, Tuple
from services.analysis.analyser import Analyser
from services.analysis.stats import StatsPDF
from services.fulltext_search.phrase import Phrase
from services.tokenization import Token
from services.fulltext_search.fulltext_search import FulltextSearch, SearchStrategy
from services.utils.timeit import timeit
from services.analysis.pdf.pua_map import PuaMap, logger
from services.analysis.pdf.page_analyser import PageAnalyser

WORDS_EXTRACT_PATTERN = re.compile(r'[a-zA-Zа-яА-ЯёЁ]+', re.UNICODE)
PUNCT_STRIP_PATTERN = re.compile(r"^[^\w\s]+|[^\w\s]+$", re.UNICODE)
MIN_OCR_CONFIDENCE_HIGHLIGHT = 40
HYPHEN_CHARS = ('-', '\u00AD')
MAX_LINE_JUMP_MERGE = 150
HORIZONTAL_INDENT_THRESHOLD = 200
MIN_CONF_FOR_MERGE = 5
USE_STEM_FALLBACK = True


class AnalyserPdf(Analyser):
    document: Optional[pymupdf.Document]
    source_path: str
    # _progress: Optional['CombinedProgress']

    def __init__(self, source_path: str):
        super().__init__()
        self.source_path = source_path
        self.document = None
        self._progress = None

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None, use_ocr: bool = False) -> dict:
        self.document = pymupdf.open(self.source_path)

        pages_to_process = len(self.document)

        # [start] Collect pages
        pua_map = PuaMap()
        pages = []

        for page_num in range(pages_to_process):
            page = self.document.load_page(page_num)
            page_analyser = PageAnalyser(page=page, pua_map=pua_map, highlight_color=self.get_highlight_color_pdf())
            page_analyser.collect()
            pages.append(page_analyser)
        # [end]

        # [start] tokenize document and run search
        whole_document_text = ''

        for page_analyser in pages:
            whole_document_text += page_analyser.to_text() + ' '

        # [start] calculate page offsets and lengths in combined text
        page_offsets: List[int] = [0]
        page_lengths: List[int] = []
        current_offset: int = 0

        for page_analyser in pages:
            page_text = page_analyser.to_text()
            page_len = len(page_text)
            page_lengths.append(page_len)
            current_offset += page_len + 1
            page_offsets.append(current_offset)
        # [end]

        all_tokens: List[Token] = FulltextSearch.tokenize_text(whole_document_text)
        phrases_list = list(self.analyse_data.phrases.values())
        search_phrases_for_search: List[Tuple[Phrase, List[Token]]] = [
            (phrase, phrase.tokens) for phrase in phrases_list
        ]
        fulltext_search = FulltextSearch(all_tokens)
        regex_patterns_dict = None

        if self.analyse_data.regex_patterns:
            regex_patterns_dict = {
                pattern.pattern_name: pattern
                for pattern in self.analyse_data.regex_patterns
            }

        phrase_results = fulltext_search.search_all(
            search_phrases_for_search, 
            SearchStrategy.FUZZY_WORDS_PUNCT,
            regex_patterns=regex_patterns_dict
        )

        # [start] todo: dev only simplify
        fts_matches = []

        for _, fts_match in phrase_results:
            fts_matches.extend(fts_match)
        # [end]

        matches = self._convert_fts_matches(fts_matches)

        # [start] determine page number for each match
        for match in matches:
            search_match = match.search_match
            start_token_idx: int = search_match.start_token_idx
            start_char_pos: int = all_tokens[start_token_idx].start

            # find page that contains the start of this match
            for page_idx in range(len(pages)):
                page_start_offset: int = page_offsets[page_idx]
                page_text_len: int = page_lengths[page_idx]
                page_end_offset: int = page_start_offset + page_text_len - 1

                if page_start_offset <= start_char_pos <= page_end_offset:
                    match.page = page_idx + 1
                    break
        # [end]

        self.stats = StatsPDF(matches)
        # [end]

        if use_ocr:
            #todo: ocr not implemented
            logger.warning(f'ocr not implemented')

        # [start] highlight matches
        # [start] highlight each match
        for match in matches:
            search_match = match.search_match
            start_token_idx: int = search_match.start_token_idx
            end_token_idx: int = search_match.end_token_idx
            start_char_pos: int = all_tokens[start_token_idx].start
            end_char_pos: int = all_tokens[end_token_idx].end

            # [start] find pages that contain this match
            for page_idx, page_analyser in enumerate(pages):
                page_start_offset: int = page_offsets[page_idx]
                page_text_len: int = page_lengths[page_idx]
                page_end_offset: int = page_start_offset + page_text_len - 1

                # check if match overlaps with this page
                match_start_in_page: int = max(start_char_pos, page_start_offset)
                match_end_in_page: int = min(end_char_pos, page_end_offset)

                if match_start_in_page > match_end_in_page:
                    continue

                # convert to local page character indices
                local_start: int = match_start_in_page - page_start_offset
                local_end: int = match_end_in_page - page_start_offset

                page_analyser.highlight_range(local_start, local_end - 1)
            # [end]
        # [end]
        # [end]

        return self._get_stats_result()

    def save(self, output_path: str) -> None:
        if self.document is None:
            return

        self.document.save(output_path, garbage=4, deflate=True, clean=True)
        self.document.close()
