from dataclasses import dataclass
from typing import List, Dict

from services.analysis import AnalysisMatchKind
from services.analysis.stats.stat_form import StatForm
from services.fulltext_search.phrase import Phrase


@dataclass(frozen=True)
class StatItemSearch:
    phrase: Phrase
    kind: AnalysisMatchKind

    def __hash__(self) -> int:
        return hash((self.phrase.phrase, self.kind))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StatItemSearch):
            return False
        return self.phrase.phrase == other.phrase.phrase and self.kind == other.kind

# think about this like a row in the search results table
@dataclass
class StatItem:
    search: StatItemSearch
    total: int
    forms: Dict[str, StatForm]
