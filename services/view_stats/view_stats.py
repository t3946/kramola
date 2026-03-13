from enum import Enum

from services.analysis.stats import StatForm
from services.enum import WordsListKey
from services.task import TaskResult

class ESublist(Enum):
    """Search strategy enum."""
    WORDS = "WORDS"
    PHRASES = "PHRASES"

class ViewStats:
    task_id: str
    task_result: dict

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.task_result = TaskResult.load(task_id)

    def _count_words(self, text: str) -> int:
        if not text or not text.strip():
            return 0

        words = text.split()
        return len(words)

    def get(self):
        stats: list[dict] = self.task_result["stats"]
        stats_grouped: dict[WordsListKey, dict[str, StatForm]] = {}

        # [start] group stats
        for stat in stats:
            list_key: WordsListKey = WordsListKey(stat["search"]["phrase"]["source_list"])
            simple_stats_list_keys = [
                WordsListKey.PROFANITY,
                WordsListKey.PROHIBITED_SUBSTANCES,
                WordsListKey.DANGEROUS,
                WordsListKey.CUSTOM,
                WordsListKey.CUSTOM_EXCLUDE,
            ]
            smart_stats_list_keys = [
                WordsListKey.EXTREMISTS_TERRORISTS,
                WordsListKey.INAGENTS,
            ]

            if list_key not in stats_grouped:
                stats_grouped[list_key] = {
                    ESublist.WORDS: {},
                    ESublist.PHRASES: {},
                }

            for form in stat["forms"].values():
                if list_key in simple_stats_list_keys:
                    text = form["form"]
                elif list_key in smart_stats_list_keys:
                    text = stat["search"]["phrase"]["phrase_original"]
                else:
                    continue

                sublist: ESublist = ESublist.PHRASES if self._count_words(text) > 1 else ESublist.WORDS

                if text not in stats_grouped[list_key]:
                    # add new stat
                    stats_grouped[list_key][sublist][text] = StatForm(
                        count=form["count"],
                        form=form["form"],
                        pages=form["pages"],
                    )
                else:
                    # update existing stat
                    stats_grouped[list_key][text].count += form["count"]

                    if form["pages"]:
                        pages = stats_grouped[list_key][sublist][text].pages
                        pages.append(form["pages"])
                        pages = list(set(pages))
                        stats_grouped[list_key][sublist][text].pages = pages
        # [end]

        return stats_grouped
