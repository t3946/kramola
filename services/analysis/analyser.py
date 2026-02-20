from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Union

from services.analysis.stats import Stats
from services.analysis.analysis_match import AnalysisMatch, AnalysisMatchKind
from services.fulltext_search.search_match import FTSRegexMatch, FTSTextMatch
from services.enum.predefined_list import ESearchSource

if TYPE_CHECKING:
    from services.analysis.analysis_data import AnalysisData

DEFAULT_HEX_HIGHLIGHT: str = "#00ff00"
ESOURCE_TO_SLUG: Dict[ESearchSource, str] = {
    ESearchSource.LIST_INAGENTS: "inagents",
    ESearchSource.LIST_EXTREMISTS_TERRORISTS: "extremists-terrorists",
    ESearchSource.LIST_PROFANITY: "profanity",
    ESearchSource.LIST_PROHIBITED_SUBSTANCES: "prohibited_substances",
    ESearchSource.LIST_SWEAR_WORDS: "swear-words",
}


class Analyser:
    analyse_data: 'AnalysisData'
    stats: Stats
    HIGHLIGHT_COLOR: Tuple[float, float, float] = (0.0, 1.0, 0.0)

    def __init__(self) -> None:
        self.stats = None
        self._highlight_color_cache: Dict[str, str] = {}

    def get_highlight_color_pdf(self) -> Tuple[float, float, float]:
        return self.HIGHLIGHT_COLOR

    def get_highlight_color_docx_val(self) -> str:
        if self.HIGHLIGHT_COLOR == (0.0, 1.0, 0.0):
            return "green"

        return "yellow"

    def _get_list_slug_from_match(self, match: AnalysisMatch) -> Optional[str]:
        if isinstance(match.search_match, FTSTextMatch):
            source = match.search_match.search_phrase.source
            if source is not None:
                return ESOURCE_TO_SLUG.get(source)

        return None

    def _get_hex_color_for_slug(self, slug: Optional[str]) -> str:
        if slug is None:
            return DEFAULT_HEX_HIGHLIGHT

        if slug in self._highlight_color_cache:
            return self._highlight_color_cache[slug]

        from services.words_list.list_colors import ListColor

        hex_color: str = ListColor.get_color_by_slug(slug)
        self._highlight_color_cache[slug] = hex_color

        return hex_color

    @staticmethod
    def _hex_to_shd_fill(hex_str: str) -> str:
        """RRGGBB for OOXML w:shd w:fill (no #)."""
        s = hex_str.strip().lstrip("#").upper()

        if len(s) == 6 and all(c in "0123456789ABCDEF" for c in s):
            return s

        return "00FF00"

    @staticmethod
    def _hex_to_pdf_rgb(hex_str: str) -> Tuple[float, float, float]:
        s = hex_str.strip().lstrip("#")

        if len(s) == 6:
            r = int(s[0:2], 16) / 255.0
            g = int(s[2:4], 16) / 255.0
            b = int(s[4:6], 16) / 255.0
            return (r, g, b)

        return (0.0, 1.0, 0.0)

    def get_highlight_color_docx_for_match(self, match: AnalysisMatch) -> str:
        """Hex as RRGGBB (no #) for w:shd w:fill."""
        slug = self._get_list_slug_from_match(match)
        hex_color = self._get_hex_color_for_slug(slug)

        return self._hex_to_shd_fill(hex_color)

    def get_highlight_color_pdf_for_match(self, match: AnalysisMatch) -> Tuple[float, float, float]:
        slug = self._get_list_slug_from_match(match)
        hex_color = self._get_hex_color_for_slug(slug)

        return self._hex_to_pdf_rgb(hex_color)

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

            # [start] filter matches unique by found tokens
            is_unique = True

            for match in analyser_matches:
                fts_m1 = match.search_match
                fts_m2 = fts_match

                # compare found tokens
                if fts_m1.start_token_idx == fts_m2.start_token_idx and fts_m1.end_token_idx == fts_m2.end_token_idx:
                    is_unique = False
            # [end]

            if is_unique:
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
