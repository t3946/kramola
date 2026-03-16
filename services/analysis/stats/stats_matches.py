from enum import Enum
from typing import Dict, Any

from services.analysis.stats.stat_form import StatForm
from services.analysis.stats.stats import Stats
from services.enum import WordsListKey


class ESublist(Enum):
    WORDS = "words"
    PHRASES = "phrases"


SIMPLE_STATS_LIST_KEYS = [
    WordsListKey.PROFANITY,
    WordsListKey.PROHIBITED_SUBSTANCES,
    WordsListKey.DANGEROUS,
    WordsListKey.CUSTOM,
    WordsListKey.CUSTOM_EXCLUDE,
]
SMART_STATS_LIST_KEYS = [
    WordsListKey.EXTREMISTS_TERRORISTS,
    WordsListKey.INAGENTS,
]


class StatsMatches(Stats):
    """stats for users"""

    def _count_words(self, text: str) -> int:
        if not text or not text.strip():
            return 0
        return len(text.split())

    def get_stats(self) -> Dict[WordsListKey, Dict[str, Any]]:
        stats_grouped: Dict[WordsListKey, Dict[str, Any]] = {}

        for match in self.matches:
            source_list = match.get("phrase", {}).get("source_list")
            if source_list is None:
                continue

            list_key = WordsListKey(source_list)
            if list_key not in SIMPLE_STATS_LIST_KEYS and list_key not in SMART_STATS_LIST_KEYS:
                continue

            if list_key not in stats_grouped:
                stats_grouped[list_key] = {
                    ESublist.WORDS.value: {},
                    ESublist.PHRASES.value: {},
                    "meta": {
                        "words": {"total": 0},
                        "phrases": {"total": 0},
                    },
                }

            if list_key in SIMPLE_STATS_LIST_KEYS:
                text = match["form"]
            else:
                text = match.get("phrase", {}).get("phrase_original") or match.get("form", "")

            sublist = ESublist.PHRASES.value if self._count_words(text) > 1 else ESublist.WORDS.value

            if text not in stats_grouped[list_key][sublist]:
                stats_grouped[list_key][sublist][text] = StatForm(
                    count=0,
                    form=match["form"],
                    pages=[],
                )

            stat_form = stats_grouped[list_key][sublist][text]
            stat_form.count += 1
            stats_grouped[list_key]["meta"][sublist]["total"] += 1

            page = match.get("page")
            if page is not None:
                stat_form.pages.append(page)
                stat_form.pages = list(set(stat_form.pages))

        return stats_grouped
