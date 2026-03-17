"""Serialize/deserialize AnalysisMatch for storing in Redis (stats-only fields)."""
from typing import List, Dict, Any

from services.analysis.analysis_match import AnalysisMatch
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch


def matches_to_dict_list(matches: List[AnalysisMatch]) -> List[Dict[str, Any]]:
    """Serialize matches to list of dicts (phrase, kind, form, page)."""
    result: List[Dict[str, Any]] = []

    for match in matches:
        phrase_dict = {}

        if isinstance(match.search_match, FTSTextMatch):
            phrase_dict = match.search_match.search_phrase.to_dict()

        if isinstance(match.search_match, FTSRegexMatch):
            phrase_dict = {
                "phrase": None,
                "phrase_original": match.search_match.get_search_str(),
                "source_list": match.search_match.regex_info.source_list.key.value,
            }

        result.append({
            "kind": match.kind.value,
            "phrase": phrase_dict,
            "form": match.found["text"],
            "page": match.page,
            "check_id": str(match.search_match.check_id),
        })

    return result
