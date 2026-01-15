from typing import List, Tuple, TYPE_CHECKING
from collections import defaultdict, Counter
from services.fulltext_search.token import Token, TokenType
from services.fulltext_search.fulltext_search import Match

if TYPE_CHECKING:
    from services.analysis.analysis_data import AnalysisData
    from services.fulltext_search.phrase import Phrase


class Analyser:
    analyse_data: 'AnalysisData'
    word_stats: defaultdict
    phrase_stats: defaultdict
    HIGHLIGHT_COLOR: Tuple[float, float, float] = (0.0, 1.0, 0.0)

    def __init__(self) -> None:
        self.word_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})
        self.phrase_stats = defaultdict(lambda: {'count': 0, 'forms': Counter()})

    def get_highlight_color_pdf(self) -> Tuple[float, float, float]:
        return self.HIGHLIGHT_COLOR

    def get_highlight_color_docx_val(self) -> str:
        if self.HIGHLIGHT_COLOR == (0.0, 1.0, 0.0):
            return 'green'

        return 'yellow'

    def set_analyse_data(self, analyse_data: 'AnalysisData') -> None:
        self.analyse_data = analyse_data

    def _update_match_statistics(self, match: Match, tokens: List[Token]) -> None:
        start_token_idx = match['start_token_idx']
        end_token_idx = match['end_token_idx']
        lemma_key = match['lemma_key']

        if match['type'] == 'phrase':
            phrase_key_str = " ".join(lemma_key)
            stats = self.phrase_stats[phrase_key_str]
            text_parts = [tokens[i].text for i in range(start_token_idx, end_token_idx + 1) if i < len(tokens)]
            found_text = "".join(text_parts).strip()
            stats['count'] += 1
            stats['forms'][found_text] += 1
        elif match['type'] == 'word':
            if lemma_key and len(lemma_key) == 1:
                word_lemma = lemma_key[0]
                stats = self.word_stats[word_lemma]

                if start_token_idx < len(tokens):
                    found_text = tokens[start_token_idx].text
                    stats['count'] += 1
                    stats['forms'][found_text.lower()] += 1

    def _convert_phrase_results_to_matches(
            self,
            phrase_results: List[Tuple[str, List[Tuple[int, int]]]],
            phrases_list: List['Phrase']
    ) -> List[Match]:
        matches: List[Match] = []
        phrase_dict = {phrase.phrase: phrase for phrase in phrases_list}

        for phrase_text, found_matches in phrase_results:
            phrase = phrase_dict.get(phrase_text)

            if phrase is None:
                continue

            search_words = [t for t in phrase.tokens if t.type == TokenType.WORD]

            if len(search_words) == 0:
                continue

            lemma_key = tuple(token.lemma for token in search_words if token.lemma)
            match_type = 'word' if len(search_words) == 1 else 'phrase'

            for start_token_idx, end_token_idx in found_matches:
                matches.append({
                    'start_token_idx': start_token_idx,
                    'end_token_idx': end_token_idx,
                    'lemma_key': lemma_key,
                    'type': match_type,
                    'match_type': 'lemma',
                })

        return matches

    def _get_stats_result(self) -> dict:
        total_matches = sum(d['count'] for d in self.word_stats.values()) + sum(
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

        return {'word_stats': final_ws, 'phrase_stats': final_ps, 'total_matches': total_matches}

