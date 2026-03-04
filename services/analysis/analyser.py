from typing import List, Tuple, TYPE_CHECKING, Union

from services.analysis.stats import Stats
from services.analysis.analysis_match import AnalysisMatch, AnalysisMatchKind
from services.fulltext_search.search_match import FTSRegexMatch, FTSTextMatch
from services.utils.color import Color
from services.words_list import WordsList

if TYPE_CHECKING:
    from services.analysis.analysis_data import AnalysisData

DEFAULT_HEX_HIGHLIGHT: str = "#00ff00"


class Analyser:
    analyse_data: 'AnalysisData'
    stats: Stats

    def __init__(self) -> None:
        self.stats = None
        self._default_color: Color = Color(DEFAULT_HEX_HIGHLIGHT)

    def get_highlight_color_pdf(self) -> Tuple[float, float, float]:
        return self._default_color.rgb()

    def _highlight_color_for_match(self, match: AnalysisMatch) -> Color:
        if isinstance(match.search_match, FTSTextMatch):
            source_list: WordsList = match.search_match.search_phrase.source_list
            return source_list.highlight_color

        return self._default_color

    def set_analyse_data(self, analyse_data: 'AnalysisData') -> None:
        self.analyse_data = analyse_data

    @staticmethod
    def _convert_fts_matches(
            fts_matches: List[Union[FTSTextMatch, FTSRegexMatch]],
    ) -> List[AnalysisMatch]:
        """
        Convert FTSMatch results to AnalysisMatch results.
        """
        analyser_matches: List[AnalysisMatch] = []

        # Create lookup dict for O(1) phrase access by text instead of O(n) list search
        for fts_match in fts_matches:
            found_text = ''.join(token.text for token in fts_match.tokens if token.text)

            # [start] Determine match kind
            match_kind = AnalysisMatchKind.WORD

            if isinstance(fts_match, FTSRegexMatch):
                match_kind = AnalysisMatchKind.REGEX

            if isinstance(fts_match, FTSTextMatch):
                if len(fts_match.tokens) > 1:
                    match_kind = AnalysisMatchKind.PHRASE
            # [end]

            # cast fts match to analysis match
            analyser_matches.append(AnalysisMatch(
                kind=match_kind,
                search_match=fts_match,
                found={
                    'text': found_text,
                    'tokens': fts_match.tokens,
                }
            ))

        return analyser_matches

    def _get_stats_result(self) -> dict:
        stats_list = self.stats.asdict() if self.stats else []
        total_matches = sum(item['total'] for item in stats_list)

        return {'stats': stats_list, 'total_matches': total_matches}
