import re
import pymupdf

from typing import List, Optional, Tuple, Dict

from services.analysis import AnalysisMatch
from services.analysis.analyser import Analyser
from services.fulltext_search.phrase import Phrase
from services.progress.combined_progress.combined_progress import CombinedProgress
from services.progress.combined_progress.process_particle import ProgressParticle
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

    _progress: Optional['CombinedProgress']

    def __init__(self, source_path: str):
        super().__init__()
        self.source_path = source_path
        self.document = None
        self._progress = None

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None, use_ocr: bool = False) -> dict:
        self.document = pymupdf.open(self.source_path)

        self._progress = CombinedProgress(task_id, [
            ProgressParticle(
                key='collect_pages',
                description='Индексация страниц',
            ),
            ProgressParticle(
                key='tokenize_test',
                description='Токенизация',
            ),
        ])

        # [start] Collect pages
        pages_to_process = len(self.document)
        pua_map = PuaMap()
        pages = []
        self._progress.add_particle()

        for page_num in range(pages_to_process):
            page = self.document.load_page(page_num)
            page_analyser = PageAnalyser(page=page, pua_map=pua_map, highlight_color=self.get_highlight_color_pdf())
            page_analyser.collect()
            pages.append(page_analyser)
            self._progress.set_particle_value('collect_pages', page_num)
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
        phrases_list = self.analyse_data.phrases
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
            search_phrases=search_phrases_for_search,
            text_strategy=SearchStrategy.FUZZY_WORDS_PUNCT,
            search_patterns=regex_patterns_dict
        )

        # [start] todo: dev only simplify
        fts_matches = []

        for _, fts_match in phrase_results:
            fts_matches.extend(fts_match)
        # [end]

        matches: List[AnalysisMatch] = self._convert_fts_matches(fts_matches)

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

        if use_ocr:
            # todo: ocr not implemented
            logger.warning(f'ocr not implemented')

        # [start] highlight matches
        # key is tuple(page, start_index, end_index)
        highlighting_map: Dict[(PageAnalyser, int, int), List[AnalysisMatch]] = {}

        for match in matches:
            search_match = match.search_match
            start_token_idx: int = search_match.start_token_idx
            end_token_idx: int = search_match.end_token_idx
            start_char_pos: int = all_tokens[start_token_idx].start
            end_char_pos: int = all_tokens[end_token_idx].end

            # [start] find pages that contain this match and highlight it
            for page_idx, page_analyser in enumerate(pages):
                page_start_offset: int = page_offsets[page_idx]
                page_text_len: int = page_lengths[page_idx]
                page_end_offset: int = page_start_offset + page_text_len - 1

                # [start] check if match overlaps with this page
                match_start_in_page: int = max(start_char_pos, page_start_offset)
                match_end_in_page: int = min(end_char_pos, page_end_offset)

                if match_start_in_page > match_end_in_page:
                    continue
                # [end]

                # convert global indices to local page character indices
                local_start: int = match_start_in_page - page_start_offset
                local_end: int = match_end_in_page - page_start_offset

                # add match into map
                key = (page_analyser, local_start, local_end - 1)

                if highlighting_map.get(key) is None:
                    highlighting_map[key] = []

                highlighting_map[key].append(match)
            # [end]

        # [start] build highlighting map
        for key, map_matches in highlighting_map.items():
            page, start, end = key
            color: Tuple[float, float, float] = self._highlight_color_for_match(map_matches[0]).rgb()

            if len(map_matches) == 1:
                page.highlight_range(start, end, map_matches[0], color)
            else:
                page.highlight_range(start, end, map_matches, color)
        # [end]
        # [end]

        return self._get_stats_result(matches)

    def save(self, output_path: str) -> None:
        if self.document is None:
            return

        self.document.save(output_path, garbage=4, deflate=True, clean=True)
        self.document.close()
