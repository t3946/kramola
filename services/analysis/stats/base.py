from typing import List
from abc import ABC
from services.analysis.analysis_match import AnalysisMatch, AnalysisMatchKind
from services.analysis.stats.stat_item import StatItem


class Stats(ABC):
    matches: List[AnalysisMatch]

    def __init__(self, matches: List[AnalysisMatch]) -> None:
        self.matches = matches

    def get(self, match_type: AnalysisMatchKind) -> List[StatItem]:
        pass
