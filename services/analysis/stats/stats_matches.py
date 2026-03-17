from enum import Enum
from typing import Dict, Any, Set

from flask import current_app

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
        # (list_key, sublist, text) -> check_ids set, form, pages list
        raw: Dict[tuple, Dict[str, Any]] = {}
        stats_grouped: Dict[WordsListKey, Dict[str, Any]] = {}
        current_app.logger.debug(self.matches)

        # mapping matches
        for match in self.matches:
            source_list = match.get("phrase", {}).get("source_list")
            list_key = WordsListKey(source_list)

            if list_key in SIMPLE_STATS_LIST_KEYS:
                text = match["form"]
            else:
                text = match.get("phrase", {}).get("phrase_original") or match.get("form", "")

            if match['kind'] == 'phrase':
                sublist = ESublist.PHRASES.value
            else:
                sublist = ESublist.WORDS.value

            key = (list_key, sublist, text)

            if key not in raw:
                raw[key] = {
                    "check_ids": set(),
                    "form": text,
                    "pages": [],
                }

            raw[key]["check_ids"].add(match["check_id"])
            page = match.get("page")

            if page is not None:
                raw[key]["pages"].append(page)

        # build stats
        for (list_key, sublist, text), data in raw.items():
            if list_key not in stats_grouped:
                stats_grouped[list_key] = {
                    ESublist.WORDS.value: {},
                    ESublist.PHRASES.value: {},
                    "meta": {
                        "words": {"total": 0},
                        "phrases": {"total": 0},
                    },
                }

            count = len(data["check_ids"])
            stats_grouped[list_key][sublist][text] = StatForm(
                count=count,
                form=data["form"],
                pages=list(set(data["pages"])),
            )
            stats_grouped[list_key]["meta"][sublist]["total"] += count

        return stats_grouped
