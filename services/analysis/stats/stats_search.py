from services.analysis import AnalysisMatchKind
from services.analysis.stats.stat_form import StatForm
from services.analysis.stats.stat_item import StatItem, StatItemSearch
from services.analysis.stats.stats import Stats
from services.fulltext_search.phrase import Phrase


class StatsSearch(Stats):
    """stats for debug"""

    def __init__(self, task_id: str) -> None:
        super().__init__(task_id)
        self._build_search_stats()

    def _build_search_stats(self) -> None:
        for match in self.matches:
            phrase = Phrase.from_dict(match["phrase"])
            kind = AnalysisMatchKind(match["kind"])
            search_item = StatItemSearch(phrase=phrase, kind=kind)
            stat_item = self.stats.get(search_item)

            if not stat_item:
                stat_item = StatItem(
                    search=search_item,
                    total=0,
                    forms={},
                )
                self.stats[search_item] = stat_item

            form_text = match["form"]
            form = stat_item.forms.get(form_text)

            if not form:
                form = StatForm(
                    count=0,
                    form=form_text,
                    pages=[],
                )
                stat_item.forms[form_text] = form

            form.count += 1

            page = match.get("page")
            if page is not None:
                form.pages.append(page)

            form.pages = list(set(form.pages))
            stat_item.total += 1

    def get_stats(self) -> list:
        return self.asdict()
