"""Shared logic for annotation/comment title and content from AnalysisMatch."""

from typing import Tuple

from models import Inagent
from models.inagents import AgentType
from services.analysis.analysis_match import AnalysisMatch
from services.enum.predefined_list import ESearchSourceAnnotTitle
from services.fulltext_search import Phrase
from services.fulltext_search.search_match import FTSTextMatch, FTSRegexMatch


def get_annot_title_content(match: AnalysisMatch) -> Tuple[str, str]:
    """Return (title, content) for PDF annot or Word comment from AnalysisMatch."""
    if isinstance(match.search_match, FTSTextMatch):
        phrase: Phrase = match.search_match.search_phrase
        content: str = phrase.phrase_original if phrase.phrase_original else phrase.phrase
        title: str = getattr(ESearchSourceAnnotTitle, phrase.source.name).value

        if phrase.source.name == ESearchSourceAnnotTitle.LIST_INAGENTS.name:
            content = ''
            inagents: list[Inagent] = Inagent.get_by_term(phrase.phrase)

            if inagents and inagents[0]:
                inagent = inagents[0]

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

        return (title, content)

    if isinstance(match.search_match, FTSRegexMatch):
        return ("Шаблон", f"«{match.search_match.regex_info.pattern_name}»")

    return ("", "")
