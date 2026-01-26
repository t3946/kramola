from typing import List
from services.analysis.analysis_match import AnalysisMatch
from services.analysis.stats.base import Stats
from services.analysis.stats.stat_item import StatItem


class StatsDocx(Stats):
    def __init__(self, matches: List[AnalysisMatch]) -> None:
        super().__init__(matches)