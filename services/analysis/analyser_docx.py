import docx
import time
from typing import List, Union, Optional, Tuple, Dict, TYPE_CHECKING
from functools import cmp_to_key

from services.analysis.stats import StatsDocx
from services.utils.intersects_at import intersects_at

if TYPE_CHECKING:
    from services.progress.docx.combined_progress import CombinedProgress

from docx.text.paragraph import Paragraph
from docx.text.hyperlink import Hyperlink
from docx.table import Table
from docx.oxml.ns import qn
from docx.oxml import OxmlElement, CT_R, CT_Text, CT_P, CT_Hyperlink

from services.analysis.analyser import Analyser
from services.analysis.analysis_match import AnalysisMatch
from services.fulltext_search.fulltext_search import FulltextSearch, SearchStrategy
from services.fulltext_search.token import Token, TokenType
from services.fulltext_search.dictionary import TokenDictionary
from services.fulltext_search.phrase import Phrase
from services.utils.timeit import timeit
from copy import deepcopy
from services.progress.docx.combined_progress import CombinedProgress, ProgressType


class AnalyserDocx(Analyser):
    document: docx.Document
    _tokenize_time_total: float
    _global_document_dictionary: Optional[TokenDictionary]
    _search_phrases: List[Phrase]
    _progress: Optional['CombinedProgress']

    def __init__(self, document: Union[docx.Document, str]):
        super().__init__()
        if isinstance(document, str):
            document = docx.Document(document)

        self.document = document
        self._tokenize_time_total = 0.0
        self._global_document_dictionary = None
        self._search_phrases = []
        self._progress = None
        self.stats = StatsDocx([])

    @staticmethod
    def __clone_run(
            source_run: CT_R,
            new_text: str,
            highlight: bool,
            highlight_val: str,
            skip_break_lines: bool = False,
    ) -> CT_R:
        new_run: CT_R = OxmlElement('w:r')

        for child in source_run:
            if skip_break_lines and child.tag == qn('w:br'):
                continue

            new_run.append(deepcopy(child))

        # update text
        text_element: CT_Text = new_run.find(qn('w:t'))
        text_element.text = new_text
        text_element.set(qn('xml:space'), 'preserve')

        # update highlight
        if highlight:
            rPr = new_run.find(qn('w:rPr'))

            if rPr is None:
                rPr = OxmlElement('w:rPr')
                new_run.insert(0, rPr)

            highlight = OxmlElement('w:highlight')
            highlight.set(qn('w:val'), highlight_val)
            rPr.append(highlight)

        return new_run

    @staticmethod
    def __isolate_new_run_xml(
            batch: List[CT_R],
            phrase_start_index: int,
            phrase_end_index: int,
            highlight_val: str
    ) -> List[CT_R]:
        # end_index-1 because in python slices index interval standard is [start, end) but not [start, end] like in the other world
        # todo: эту хуйню с индексами надо бы убрать я думаю, но для начала надо починить баги
        phrase_end_index -= 1

        # after Run split operation, batch need to be updated
        new_batch = []

        # [start] find run by char index
        proceed_chars = 0

        for run_source in batch:
            # specification suppose w:r could contain multiple w:t, but ms word automatically reduces it to: 1 w:r = 1 w:t
            source_run_text_element: CT_Text = run_source.find(qn('w:t'))

            if source_run_text_element is None:
                proceed_chars += len(run_source.text)
                new_batch.append(run_source)
                continue

            # skip line break "\n" in run if it exists
            proceed_chars += run_source.text.find(source_run_text_element.text)

            text: str = source_run_text_element.text
            run_source_text_len = len(run_source.text)
            run_start_index = proceed_chars
            run_end_index = run_start_index + len(text)

            intersection = intersects_at((run_start_index, run_end_index), (phrase_start_index, phrase_end_index))

            if intersection:
                intersection_len = intersection[1] - intersection[0]
                run_relative_char_start_index: int = intersection[0] - proceed_chars
                run_relative_char_end_index: int = run_relative_char_start_index + intersection_len

                # [start] split run text on three new parts: before, match and after
                part_before_match: str = text[:run_relative_char_start_index]
                part_match: str = text[run_relative_char_start_index:run_relative_char_end_index+1]
                part_after_match: str = text[run_relative_char_end_index+1:]

                # needs to avoid cases "This is an apple" -> "This is anapple"
                source_run_text_element.set(qn('xml:space'), 'preserve')

                run_match = AnalyserDocx.__clone_run(run_source, part_match, True, highlight_val, skip_break_lines=True)
                run_after = AnalyserDocx.__clone_run(run_source, part_after_match, False, highlight_val, skip_break_lines=True)
                source_run_text_element.text = part_before_match
                run_source.addnext(run_match)
                run_match.addnext(run_after)
                # [end]

                new_batch.append(run_source)
                new_batch.append(run_match)
                new_batch.append(run_after)
            else:
                new_batch.append(run_source)

            proceed_chars += run_source_text_len
        # [end]

        return new_batch

    def __search_all_phrases(
            self,
            source_tokens: List[Token],
            search_phrases: List[Phrase]
    ) -> List[AnalysisMatch]:
        """Search all phrases using optimized strategy with dictionary."""
        fulltext_search = FulltextSearch(source_tokens)
        search_phrases_for_search: List[Tuple[str, List[Token]]] = [
            (phrase.phrase, phrase.tokens) for phrase in search_phrases
        ]
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

        # [start] sort matches by position in text
        def cmp(m1: AnalysisMatch, m2: AnalysisMatch):
            return m1.search_match.start_token_idx - m2.search_match.start_token_idx

        matches = sorted(matches, key=cmp_to_key(cmp))
        # [end]

        return matches

    def __process_batch(self, batch: List[CT_R]) -> None:
        # [start] find matches in concatenated batch text
        text = ''.join([run.text for run in batch])
        start_time = time.time()
        source_tokens: List[Token] = FulltextSearch.tokenize_text(text)
        self._tokenize_time_total += time.time() - start_time

        matches: List[AnalysisMatch] = self.__search_all_phrases(
            source_tokens,
            self._search_phrases
        )
        # [end]

        highlight_val: str = self.get_highlight_color_docx_val()

        for match in matches:
            self.stats.add(match)
            search_match = match.search_match
            start_token_idx = search_match.start_token_idx
            end_token_idx = search_match.end_token_idx

            for i in range(start_token_idx, end_token_idx + 1):
                token = source_tokens[i]
                batch = self.__isolate_new_run_xml(batch, token.start, token.end, highlight_val)

    @staticmethod
    def __split_on_batches(element: Union[CT_P, CT_Hyperlink]) -> List[List[CT_R]]:
        batches = []
        batch_runs = []

        for child in element.r_lst:
            batch_runs.append(child)

        if len(batch_runs) > 0:
            batches.append(batch_runs)

        return batches

    def __analyse_paragraph(self, paragraph: Paragraph) -> None:
        batches = AnalyserDocx.__split_on_batches(paragraph._element)

        for batch in batches:
            self.__process_batch(batch)

        hyperlinks: List[Hyperlink] = paragraph.hyperlinks

        for link in hyperlinks:
            self.__analyze_link(link._element)

    def __analyze_link(self, link: CT_Hyperlink) -> None:
        batches = AnalyserDocx.__split_on_batches(link)

        for batch in batches:
            self.__process_batch(batch)

    def __build_global_dictionary(self) -> TokenDictionary:
        """Build dictionary from entire document text."""
        if self._progress:
            self._progress.setValue(0, ProgressType.PREPARATION)

        paragraphs: List[Paragraph] = self.document.paragraphs
        tables: List[Table] = self.document.tables

        # [start] count total paragraphs for progress
        total_paragraphs = len(paragraphs)

        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    total_paragraphs += len(cell.paragraphs)

        if self._progress:
            self._progress.setMax(total_paragraphs, ProgressType.PREPARATION)
        # [end]

        # [start] tokenize and build dictionary gradually
        all_tokens: List[Token] = []

        for paragraph in paragraphs:
            paragraph_tokens = FulltextSearch.tokenize_text(paragraph.text)
            all_tokens.extend(paragraph_tokens)

            if self._progress:
                self._progress.add(1, ProgressType.PREPARATION)

        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph_tokens = FulltextSearch.tokenize_text(paragraph.text)
                        all_tokens.extend(paragraph_tokens)

                        if self._progress:
                            self._progress.add(1, ProgressType.PREPARATION)
        # [end]

        dictionary = TokenDictionary(all_tokens)

        return dictionary

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
                # [start] update progress - all progress updates in one place
                if self._progress:
                    self._progress.add(1, ProgressType.PREPARATION)
                # [end]
                continue

            filtered_words = dictionary.filter_tokens(search_words)

            if len(filtered_words) == len(search_words):
                filtered_phrases.append(phrase)

            # [start] update progress - all progress updates in one place
            if self._progress:
                self._progress.add(1, ProgressType.PREPARATION)
            # [end]

        return filtered_phrases

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None) -> dict:
        self.stats = StatsDocx([])
        self._search_phrases = []

        paragraphs: List[Paragraph] = self.document.paragraphs
        tables: List[Table] = self.document.tables

        # [start] count progress max
        self._progress = None

        if task_id is not None:
            phrases_list = list(self.analyse_data.phrases.values())
            preparation_max_value = len(phrases_list) + 1  # +1 for building dictionary

            total_table_paragraphs = 0

            for table in tables:
                for row in table.rows:
                    for cell in row.cells:
                        total_table_paragraphs += len(cell.paragraphs)

            search_max_value = len(paragraphs) + total_table_paragraphs
            self._progress = CombinedProgress(task_id, preparation_max_value, search_max_value)
        # [end]

        # [start] build global dictionary and filter search phrases by it
        self._global_document_dictionary = self.__build_global_dictionary()
        phrases_list = list(self.analyse_data.phrases.values())
        self._search_phrases = self.__filter_phrases_by_dictionary(
            phrases_list,
            self._global_document_dictionary
        )
        # [end]

        # process paragraphs
        for paragraph in paragraphs:
            self.__analyse_paragraph(paragraph)
            # [start] update progress - all progress updates in one place
            if self._progress:
                self._progress.add(1, ProgressType.SEARCH)
            # [end]

        # process tables
        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_paragraphs: List[Paragraph] = cell.paragraphs

                    for paragraph in cell_paragraphs:
                        self.__analyse_paragraph(paragraph)
                        # [start] update progress - all progress updates in one place
                        if self._progress:
                            self._progress.add(1, ProgressType.SEARCH)
                        # [end]

        if self._progress:
            self._progress.flush()
            self._progress.clear()

        return self._get_stats_result()

    def save(self, output_path: str) -> None:
        self.document.save(output_path)
