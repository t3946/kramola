from typing import Any

from flask import render_template

from models import ListRecord
from services.analysis import AnalysisMatchKind
from services.enum.enum_words_list_key import WordsListKey
from services.enum.predefined_list import ESearchSourceAnnotTitle
from services.analysis.stats import StatsSearch, StatsMatches
from services.task import TaskResult
from services.words_list.list_colors import DEFAULT_LIST_COLOR_HEX


class ResultsController:
    _EXCLUDED_TEMPLATE_KEYS = {
        'task_id', 'word_stats_sorted', 'phrase_stats_sorted', '_task_id_ref',
        'word_stats', 'phrase_stats', 'stats'
    }

    @staticmethod
    def _split_stats_by_kind(stats: list) -> tuple[list, list, list]:
        word_stats: list = []
        phrase_stats: list = []
        pattern_stats: list = []

        for stat_item in stats:
            kind_value = stat_item.get('search', {}).get('kind')

            if kind_value == AnalysisMatchKind.WORD.value:
                word_stats.append(stat_item)
            elif kind_value == AnalysisMatchKind.PHRASE.value:
                phrase_stats.append(stat_item)
            elif kind_value == AnalysisMatchKind.REGEX.value:
                pattern_stats.append(stat_item)

        return word_stats, phrase_stats, pattern_stats

    @classmethod
    def render(cls, task_id: str) -> str:
        last_result_data = TaskResult.load(task_id)
        task_id_for_template = last_result_data.get('_task_id_ref', task_id)
        template_data = {
            k: v for k, v in last_result_data.items()
            if k not in cls._EXCLUDED_TEMPLATE_KEYS
        }
        stats_search = StatsSearch(task_id).get_stats()
        stats_matches = StatsMatches(task_id).get_stats()
        word_stats, phrase_stats, pattern_stats = cls._split_stats_by_kind(stats_search)

        # [start] get colors
        list_colors: dict[WordsListKey, str] = {}
        list_records = ListRecord.query.all()

        for list_record in list_records:
            key = WordsListKey(list_record.name)
            list_colors[key] = list_record.color

        if WordsListKey.CUSTOM not in list_colors:
            list_colors[WordsListKey.CUSTOM] = DEFAULT_LIST_COLOR_HEX
        # [end]

        return render_template(
            'tool_highlight/results.html',
            task_id=task_id_for_template,
            pattern_stats=pattern_stats,
            stats=stats_search,
            search_source_type=WordsListKey,
            e_words_list_key=WordsListKey,
            e_search_source_annot_title=ESearchSourceAnnotTitle,
            list_colors=list_colors,
            search_result_stats=stats_matches,
            word_stats=word_stats,
            phrase_stats=phrase_stats,
            **template_data,
        )
