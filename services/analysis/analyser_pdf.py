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

    def __find_word_match_multi_stage(
            self,
            doc_word_text: str,
            search_lemmas_set: set,
            search_stems_set: set
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        if not doc_word_text or not isinstance(doc_word_text, str):
            return False, None, None

        doc_word_lower = doc_word_text.lower().strip()
        match = PUNCT_STRIP_PATTERN.sub('', doc_word_lower)
        final_letters_match = WORDS_EXTRACT_PATTERN.search(match)

        if final_letters_match:
            word_for_morph = final_letters_match.group(0)
        else:
            word_for_morph = ""

        if not word_for_morph:
            return False, None, None

        doc_lemma = _get_lemma(word_for_morph)
        doc_stem = None

        if USE_STEM_FALLBACK:
            doc_stem = _get_stem(word_for_morph)

        if not doc_lemma:
            doc_lemma = doc_word_lower

        if doc_lemma in search_lemmas_set:
            is_russian = bool(CYRILLIC_PATTERN.search(doc_lemma or ''))
            stop_words_set = STOP_WORDS_RU if is_russian else STOP_WORDS_EN

            if doc_lemma in stop_words_set:
                return False, None, None

            return True, doc_lemma, 'lemma'

        if USE_STEM_FALLBACK and doc_stem and doc_stem in search_stems_set:
            is_russian = bool(CYRILLIC_PATTERN.search(doc_lemma or ''))
            stop_words_set = STOP_WORDS_RU if is_russian else STOP_WORDS_EN

            if doc_lemma in stop_words_set:
                return False, None, None

            return True, doc_lemma, 'stem'

        return False, None, None

    def __get_bounding_rect(self, rects_list_of_tuples: List[Tuple]) -> Optional[pymupdf.Rect]:
        if not rects_list_of_tuples:
            return None

        min_x0, min_y0 = float('inf'), float('inf')
        max_x1, max_y1 = float('-inf'), float('-inf')
        valid_rect_found = False

        for r_tuple in rects_list_of_tuples:
            try:
                x0, y0, x1, y1 = r_tuple

                if x0 < x1 and y0 < y1:
                    min_x0 = min(min_x0, x0)
                    min_y0 = min(min_y0, y0)
                    max_x1 = max(max_x1, x1)
                    max_y1 = max(max_y1, y1)
                    valid_rect_found = True
            except (TypeError, ValueError):
                continue

        if not valid_rect_found:
            return None

        return pymupdf.Rect(min_x0, min_y0, max_x1, max_y1)

    def __rects_overlap_significantly(
            self,
            rects1_list_tuples: List[Tuple],
            rects2_list_tuples: List[Tuple],
            threshold: float = 0.5
    ) -> bool:
        bbox1 = self.__get_bounding_rect(rects1_list_tuples)
        bbox2 = self.__get_bounding_rect(rects2_list_tuples)

        if bbox1 is None or bbox2 is None or bbox1.is_empty or bbox2.is_empty:
            return False

        intersection_rect = bbox1 & bbox2

        if intersection_rect.is_empty:
            return False

        area1 = bbox1.get_area()
        area2 = bbox2.get_area()
        intersection_area = intersection_rect.get_area()

        if area1 <= 1e-9 or area2 <= 1e-9:
            return False

        smaller_area = min(area1, area2)
        overlap_ratio = intersection_area / smaller_area

        return overlap_ratio >= threshold

    def __deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        if not candidates:
            return []

        unique_candidates = []
        processed_indices = set()
        candidates.sort(key=lambda c: (c['source'] != 'fitz', -float(c.get('confidence', -1.0))))

        for i in range(len(candidates)):
            if i in processed_indices:
                continue

            current_candidate = candidates[i]
            overlapping_group = [current_candidate]
            indices_in_group = {i}

            for j in range(i + 1, len(candidates)):
                if j in processed_indices:
                    continue

                other_candidate = candidates[j]

                if self.__rects_overlap_significantly(current_candidate['rects'], other_candidate['rects']):
                    overlapping_group.append(other_candidate)
                    indices_in_group.add(j)

            winner = overlapping_group[0]
            unique_candidates.append(winner)
            processed_indices.update(indices_in_group)

        return unique_candidates

    def __merge_hyphenated_ocr_words(self, ocr_df: pd.DataFrame) -> List[Dict]:
        if ocr_df is None or ocr_df.empty:
            return []

        required_cols = ['level', 'text', 'conf', 'left', 'top', 'width', 'height']

        if not all(col in ocr_df.columns for col in required_cols):
            return [
                {
                    'text': row.get('text', ''),
                    'conf': float(row.get('conf', -1.0)),
                    'level': int(row.get('level', -1)),
                    'is_merged': False,
                    'original_indices': [index]
                }
                for index, row in ocr_df.iterrows()
                if int(row.get('level', -1)) == 5
            ]

        words_df = ocr_df[
            (ocr_df['level'].astype(int) == 5) &
            (pd.to_numeric(ocr_df['conf'], errors='coerce') >= MIN_CONF_FOR_MERGE) &
            (ocr_df['text'].notna()) &
            (ocr_df['text'].astype(str).str.strip() != '')
            ].copy()

        if words_df.empty:
            return []

        for col in ['left', 'top', 'width', 'height', 'conf']:
            words_df[col] = pd.to_numeric(words_df[col], errors='coerce')

        words_df.dropna(subset=['left', 'top', 'width', 'height', 'conf'], inplace=True)

        for col in ['left', 'top', 'width', 'height']:
            words_df[col] = words_df[col].astype(int)

        words_df['conf'] = words_df['conf'].astype(float)

        if words_df.empty:
            return []

        words_df = words_df.sort_values(by=['top', 'left'])
        output_words = []
        merged_indices = set()
        word_indices = list(words_df.index)

        for i in range(len(word_indices)):
            idx1 = word_indices[i]

            if idx1 in merged_indices:
                continue

            row1 = words_df.loc[idx1]
            text1 = str(row1['text']).strip()

            if not text1:
                continue

            ends_with_hyphen = text1.endswith(HYPHEN_CHARS)
            found_merge = False

            if ends_with_hyphen:
                for j in range(i + 1, len(word_indices)):
                    idx2 = word_indices[j]

                    if idx2 in merged_indices:
                        continue

                    row2 = words_df.loc[idx2]
                    text2 = str(row2['text']).strip()

                    if not text2:
                        continue

                    is_below = row2['top'] > row1['top']
                    vertical_dist_ok = abs(row2['top'] - row1['top']) < MAX_LINE_JUMP_MERGE
                    is_left_aligned = row2['left'] < HORIZONTAL_INDENT_THRESHOLD

                    if is_below and vertical_dist_ok and is_left_aligned:
                        merged_text = text1.rstrip(''.join(HYPHEN_CHARS)) + text2
                        min_confidence = min(row1['conf'], row2['conf'])
                        output_words.append({
                            'text': merged_text,
                            'conf': min_confidence,
                            'level': 5,
                            'is_merged': True,
                            'original_indices': [idx1, idx2]
                        })
                        merged_indices.add(idx1)
                        merged_indices.add(idx2)
                        found_merge = True
                        break

            if not found_merge:
                output_words.append({
                    'text': text1,
                    'conf': row1['conf'],
                    'level': 5,
                    'is_merged': False,
                    'original_indices': [idx1]
                })

        return output_words

    def __build_global_dictionary(self, text: str) -> TokenDictionary:
        """Build dictionary from entire document text."""
        all_tokens: List[Token] = FulltextSearch.tokenize_text(text)
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
                continue

            filtered_words = dictionary.filter_tokens(search_words)

            if len(filtered_words) == len(search_words):
                filtered_phrases.append(phrase)

        return filtered_phrases

    def __process_page(
            self,
            page: pymupdf.Page,
            page_num: int,
            logical_words_on_page: List[Dict],
            use_ocr: bool
    ) -> None:
        page_rect_fitz = page.rect
        highlighted_rects_on_page = []
        page_word_candidates = []
        page_word_candidates_ocr_processed = []

        for word_data in logical_words_on_page:
            word_text_fitz = word_data.get('text', '').strip()
            word_rects_fitz = word_data.get('rects', [])

            if not word_text_fitz or not word_rects_fitz:
                continue

            page_word_candidates.append({
                'text': word_text_fitz,
                'rects': word_rects_fitz,
                'source': 'fitz',
                'confidence': 100.0
            })

        if use_ocr:
            try:
                ocr_data, ocr_matrix, _ = ocr_page(page, languages=OCR_LANGUAGES, dpi=OCR_DPI)

                if ocr_data is not None and not ocr_data.empty and ocr_matrix is not None:
                    processed_ocr_words = self.__merge_hyphenated_ocr_words(ocr_data)

                    try:
                        inverse_ocr_matrix = ~ocr_matrix
                        matrix_valid = True
                    except ValueError:
                        matrix_valid = False

                    if matrix_valid:
                        for word_info in processed_ocr_words:
                            ocr_text = word_info['text']
                            ocr_conf = word_info['conf']
                            original_indices = word_info['original_indices']

                            if ocr_conf < MIN_OCR_CONFIDENCE_HIGHLIGHT:
                                continue

                            ocr_rect_tuples = []
                            valid_coords_for_word = True

                            for index in original_indices:
                                try:
                                    row = ocr_data.loc[index]
                                    left, top, width, height = int(row['left']), int(row['top']), int(
                                        row['width']), int(row['height'])

                                    if width <= 0 or height <= 0:
                                        valid_coords_for_word = False
                                        break

                                    img_rect = pymupdf.Rect(left, top, left + width, top + height)
                                    pdf_rect = img_rect * inverse_ocr_matrix
                                    pdf_rect.normalize()
                                    pdf_rect = pdf_rect & page_rect_fitz

                                    if pdf_rect and not pdf_rect.is_empty and pdf_rect.width > 1e-3 and pdf_rect.height > 1e-3:
                                        ocr_rect_tuples.append(pdf_rect.irect)
                                    else:
                                        valid_coords_for_word = False
                                        break
                                except (KeyError, ValueError, TypeError):
                                    valid_coords_for_word = False
                                    break

                            if valid_coords_for_word and ocr_rect_tuples:
                                page_word_candidates_ocr_processed.append({
                                    'text': ocr_text,
                                    'rects': ocr_rect_tuples,
                                    'source': 'ocr',
                                    'confidence': ocr_conf
                                })
            except Exception:
                pass

        all_page_word_candidates = page_word_candidates + page_word_candidates_ocr_processed
        unique_page_word_candidates = self.__deduplicate_candidates(all_page_word_candidates)

        search_lemmas_set = set()
        search_stems_set = set()

        for phrase in self._search_phrases:
            search_words = [t for t in phrase.tokens if t.type == TokenType.WORD]

            if len(search_words) == 1:
                word_token = search_words[0]

                if word_token.lemma:
                    search_lemmas_set.add(word_token.lemma)

                if word_token.stem and USE_STEM_FALLBACK:
                    search_stems_set.add(word_token.stem)

        for candidate in unique_page_word_candidates:
            candidate_text = candidate['text']
            candidate_rects_tuples = candidate['rects']

            is_match, match_lemma, _ = self.__find_word_match_multi_stage(
                candidate_text,
                search_lemmas_set,
                search_stems_set
            )

            if is_match:
                candidate_bbox = self.__get_bounding_rect(candidate_rects_tuples)

                if candidate_bbox is None or candidate_bbox.is_empty:
                    continue

                overlaps_existing = False
                check_bbox = candidate_bbox + (-1, -1, 1, 1)
                overlap_threshold_area_ratio = 0.2

                for existing_hl_rect in highlighted_rects_on_page:
                    if check_bbox.intersects(existing_hl_rect):
                        intersection = check_bbox & existing_hl_rect
                        intersection_area = intersection.get_area()
                        bbox_area = candidate_bbox.get_area()

                        if bbox_area > 1e-5 and (intersection_area / bbox_area > overlap_threshold_area_ratio):
                            overlaps_existing = True
                            break
                        elif bbox_area <= 1e-5 and intersection_area > 1e-5:
                            overlaps_existing = True
                            break

                if not overlaps_existing:
                    current_word_rects_highlighted = []
                    quads_added_count_word = 0

                    for rect_tuple in candidate_rects_tuples:
                        try:
                            rect = pymupdf.Rect(rect_tuple)

                            if rect.is_empty:
                                continue

                            highlight = page.add_highlight_annot(rect)

                            if highlight:
                                highlight.set_colors(stroke=HIGHLIGHT_COLOR_PDF)
                                highlight.update(opacity=0.4)
                                quads_added_count_word += 1
                                current_word_rects_highlighted.append(rect)
                        except Exception:
                            pass

                    if quads_added_count_word > 0:
                        stats_word = self.word_stats[match_lemma]
                        stats_word['count'] += 1
                        stats_word['forms'][candidate_text.lower()] += 1
                        highlighted_rects_on_page.extend(current_word_rects_highlighted)

        fitz_tokens_for_phrases = []

        for word_data in logical_words_on_page:
            text = word_data.get('text', '').strip()
            rects = word_data.get('rects', [])

            if text and rects:
                fitz_tokens_for_phrases.append({'text': text, 'rects': rects})

        if self._search_phrases and fitz_tokens_for_phrases:
            for phrase in self._search_phrases:
                search_words = [t for t in phrase.tokens if t.type == TokenType.WORD]

                if len(search_words) < 2:
                    continue

                target_len = len(search_words)

                if target_len > len(fitz_tokens_for_phrases):
                    continue

                for i in range(len(fitz_tokens_for_phrases) - target_len + 1):
                    window_tokens = fitz_tokens_for_phrases[i: i + target_len]
                    window_lemmas = []
                    valid_phrase_lemmas = True

                    for tok in window_tokens:
                        lemma = _get_lemma(tok['text'])

                        if lemma is None:
                            valid_phrase_lemmas = False
                            break

                        window_lemmas.append(lemma)

                    phrase_lemmas = tuple(token.lemma for token in search_words if token.lemma)

                    if valid_phrase_lemmas and tuple(window_lemmas) == phrase_lemmas:
                        phrase_text = " ".join(tok['text'] for tok in window_tokens)
                        phrase_rects_tuples = list(itertools.chain.from_iterable(tok['rects'] for tok in window_tokens))
                        phrase_bbox = self.__get_bounding_rect(phrase_rects_tuples)

                        if phrase_bbox is None or phrase_bbox.is_empty:
                            continue

                        overlaps_existing_highlight = False
                        check_phrase_bbox = phrase_bbox + (-1, -1, 1, 1)
                        overlap_threshold_area_ratio = 0.2
                        phrase_bbox_area = phrase_bbox.get_area()

                        for existing_hl_rect in highlighted_rects_on_page:
                            if check_phrase_bbox.intersects(existing_hl_rect):
                                intersection = check_phrase_bbox & existing_hl_rect
                                intersection_area = intersection.get_area()

                                if phrase_bbox_area > 1e-5 and (
                                        intersection_area / phrase_bbox_area > overlap_threshold_area_ratio):
                                    overlaps_existing_highlight = True
                                    break
                                elif phrase_bbox_area <= 1e-5 and intersection_area > 1e-5:
                                    overlaps_existing_highlight = True
                                    break

                        if not overlaps_existing_highlight:
                            current_phrase_rects_highlighted = []
                            quads_added_count_phrase = 0

                            for rect_tuple in phrase_rects_tuples:
                                try:
                                    rect = pymupdf.Rect(rect_tuple)

                                    if rect.is_empty:
                                        continue

                                    highlight_annot = page.add_highlight_annot(rect)

                                    if highlight_annot:
                                        highlight_annot.set_colors(stroke=HIGHLIGHT_COLOR_PDF)
                                        highlight_annot.update(opacity=0.4)
                                        quads_added_count_phrase += 1
                                        current_phrase_rects_highlighted.append(rect)
                                except Exception:
                                    pass

                            if quads_added_count_phrase > 0:
                                phrase_key_str = " ".join(phrase_lemmas)
                                stats_phrase = self.phrase_stats[phrase_key_str]
                                stats_phrase['count'] += 1
                                stats_phrase['forms'][phrase_text.strip()] += 1
                                highlighted_rects_on_page.extend(current_phrase_rects_highlighted)

    @timeit
    def analyse_and_highlight(self, task_id: Optional[str] = None, use_ocr: bool = False) -> dict:
        self.word_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.phrase_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.document = pymupdf.open(self.source_path)

        # [start] Collect pages
        pua_map = PuaMap()
        pages = []

        for page_num in range(len(self.document)):
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
