from typing import List, Dict, Any
from abc import ABC
from dataclasses import asdict

from services.analysis.stats.stat_item import StatItem, StatItemSearch
from services.analysis.stats.stat_form import StatForm
from services.fulltext_search.phrase import Phrase
from services.task import TaskResult


class Stats(ABC):
    matches: List[Dict[str, Any]]
    stats: Dict[StatItemSearch, StatItem]

    def __init__(self, task_id: str) -> None:
        self.matches = []
        self.stats = {}
        self._load(task_id)

    def _load(self, task_id: str) -> None:
        task_result = TaskResult.load(task_id)
        if task_result:
            self.matches = task_result.get("matches", [])

    def asdict(self) -> List[dict]:
        stats_list = []

        for search_item, stat_item in self.stats.items():
            stat_dict = asdict(stat_item)
            stat_dict["search"] = {
                "phrase": search_item.phrase.to_dict(),
                "kind": search_item.kind.value,
            }
            stats_list.append(stat_dict)

        return stats_list
