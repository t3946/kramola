from abc import ABC
from typing import ClassVar, List
from sqlalchemy import or_

from models import Inagent
from models.inagents import AgentType
from services.enum import WordsListKey
from services.fulltext_search.phrase import Phrase
from services.words_list import WordsList


def _inagents_active_filter(query):
    i_d = Inagent.include_minjust_date
    e_d = Inagent.exclude_minjust_date
    return query.filter(
        or_(
            (i_d.isnot(None)) & (e_d.is_(None)),
            (i_d.isnot(None)) & (e_d.isnot(None)) & (i_d > e_d),
        )
    )


class ListInagents(WordsList):
    """Base for loading inagents search_terms from DB, merged into list[Phrase]."""

    key = WordsListKey.INAGENTS
    agent_types: ClassVar[List[AgentType]]

    def load(self) -> list[Phrase]:
        query = Inagent.query.with_entities(
            Inagent.full_name,
            Inagent.search_terms
        )

        if self.agent_types:
            query = query.filter(Inagent.agent_type.in_(self.agent_types))

        query = _inagents_active_filter(query)
        rows = query.all()
        phrases = []

        for (full_name, terms) in rows:
            if not isinstance(terms, list):
                terms = []

            for text in terms:
                phrase = Phrase(
                    phrase=text,
                    source_list=self,
                    phrase_original=full_name
                )

                phrases.append(phrase)

        return phrases

    def count_phrases(self) -> int:
        query = Inagent.query
        if self.agent_types:
            query = query.filter(Inagent.agent_type.in_(self.agent_types))
        query = _inagents_active_filter(query)
        return query.count()


class ListInagentsAll(ListInagents):
    """All inagents (for admin menu count)."""

    agent_types = list(AgentType)
