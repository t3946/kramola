from dataclasses import dataclass
from typing import List, Dict

from services.analysis import AnalysisMatchKind
from services.analysis.stats.stat_form import StatForm

@dataclass(frozen=True)
class StatItemSearch:
    text: str
    kind: AnalysisMatchKind

# think about this like a row in the search results table
@dataclass
class StatItem:
    search: StatItemSearch
    total: int
    forms: Dict[str, StatForm]
