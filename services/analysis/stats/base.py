from typing import List, Dict
from abc import ABC, abstractmethod
from services.analysis.analysis_match import AnalysisMatch, AnalysisMatchKind
from services.analysis.stats.stat_item import StatItem, StatItemSearch
from dataclasses import asdict
from services.analysis.stats.stat_form import StatForm


class Stats(ABC):
    matches: List[AnalysisMatch]
    stats: Dict[StatItemSearch, StatItem]

    def __init__(self, matches: List[AnalysisMatch]) -> None:
        self.matches = matches
        self.stats = {}

        for match in matches:
            self.add(match)

    def get(self, match_type: AnalysisMatchKind) -> List[StatItem]:
        pass

    def asdict(self) -> List[dict]:
        stats_list = []

        for search_item, stat_item in self.stats.items():
            stat_dict = asdict(stat_item)
            stat_dict['search'] = asdict(search_item)
            stat_dict['search']['kind'] = search_item.kind.value
            stats_list.append(stat_dict)

        return stats_list

    def add(self, match: AnalysisMatch):
        search_item = StatItemSearch(
            text=match.search_match.get_search_str(),
            kind=match.kind
        )
        stat_item = self.stats.get(search_item)

        if not stat_item:
            stat_item = StatItem(
                search=search_item,
                total=0,
                forms={},
            )

            self.stats[search_item] = stat_item

        # [start] add form
        form_text = match.found['text']
        form = stat_item.forms.get(form_text)

        if not form:
            form = StatForm(
                form=form_text,
                count=0,
                pages=[],
            )

            stat_item.forms[form_text] = form

        form.count += 1
        # form.pages.append(1)
        form.pages = list(set(form.pages))
        # [end]

        stat_item.total += 1