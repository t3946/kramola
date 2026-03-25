"""Shared logic for annotation/comment title and content from AnalysisMatch."""

from typing import Tuple, List, Union, Optional

from models import Inagent
from models.inagents import AgentType
from services.analysis.analysis_match import AnalysisMatch
from services.enum.predefined_list import ESearchSourceAnnotTitle
from services.fulltext_search import Phrase
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch, FTSMatch
from services.words_list import WordsList
from services.words_list.list_profanity import ListProfanity


def get_annot_title_content(match: AnalysisMatch) -> Tuple[str, str]:
    """Return (title, content) for PDF annot or Word comment from AnalysisMatch."""
    if isinstance(match.search_match, FTSTextMatch):
        phrase: Phrase = match.search_match.search_phrase
        content: str = phrase.phrase_original if phrase.phrase_original else phrase.phrase

        if phrase.source_list is None:
            return "Список пользователя", content

        title: str = getattr(ESearchSourceAnnotTitle, phrase.source_list.key.name).value

        if phrase.source_list.key.name == ESearchSourceAnnotTitle.INAGENTS.name:
            content = ''
            inagent: Union[Inagent, None] = phrase.model

            if inagent:
                if inagent.agent_type == AgentType.FIZ.value:
                    content = "\n".join([
                        "Иноагент",
                        f"{inagent.full_name}",
                        f"Дата рождения: {inagent.birth_date}",
                        "",
                        "Деятельность: нет",
                        f"В реестре с: {inagent.include_minjust_date}",
                        "",
                        f"Основание: {inagent.include_reason}"
                    ])
                else:
                    content = "\n".join([
                        "Иноагент",
                        f"{inagent.full_name}",
                        "",
                        "Деятельность: нет",
                        f"В реестре с: {inagent.include_minjust_date}",
                        "",
                        f"Основание: {inagent.include_reason}"
                    ])

        return title, content

    if isinstance(match.search_match, FTSRegexMatch):
        return "Шаблон", f"«{match.search_match.regex_info.pattern_name}»"

    return "", ""


def get_multiple_get_annot_title_content(matches: List[AnalysisMatch]) -> Tuple[str, str]:
    # [start] reduce profanity matches
    filtered_matches: List[AnalysisMatch] = []
    profanity_included = False

    for match in matches:
        fts_match: FTSMatch = match.search_match
        source_list: Optional[WordsList] = None

        if isinstance(fts_match, FTSTextMatch):
            phrase: Phrase = fts_match.search_phrase

            if phrase is None:
                continue

            source_list = phrase.source_list
        elif isinstance(fts_match, FTSRegexMatch):
            source_list = fts_match.regex_info.source_list

        # take only one profanity in filtered matches
        if source_list and isinstance(source_list, ListProfanity):
            if profanity_included:
                continue

            profanity_included = True

        filtered_matches.append(match)

    matches = filtered_matches
    # [end]

    # simplify output if possible
    if len(matches) == 1:
        return get_annot_title_content(matches[0])

    title = f"{len(matches)} совпадений"
    content = ""

    for i, match in enumerate(matches):
        match_title, match_content = get_annot_title_content(match)

        if len(content):
            content += "\n\n"

        content += f"{i + 1}. {match_title}:"
        content += "\n"
        content += f"«{match_content}»"

    return title, content
