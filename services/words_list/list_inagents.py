from typing import ClassVar, List

from sqlalchemy import or_

from models import Inagent
from models.inagents import AgentType
from services.enum.predefined_list import ESearchSource
from services.fulltext_search.phrase import Phrase


class ListInagents:
    """Base for loading inagents search_terms from DB, merged into list[Phrase]."""

    agent_types: ClassVar[List[AgentType]] = []

    def load(self) -> list[Phrase]:
        query = Inagent.query.with_entities(
            Inagent.full_name,
            Inagent.search_terms
        )

        if self.agent_types:
            query = query.filter(Inagent.agent_type.in_(self.agent_types))

        # [start] filter only active inagents
        i_d = Inagent.include_minjust_date
        e_d = Inagent.exclude_minjust_date
        # only "Числится": (i_d and not e_d) or (i_d and e_d and i_d > e_d)
        query = query.filter(
            or_(
                (i_d.isnot(None)) & (e_d.is_(None)),
                (i_d.isnot(None)) & (e_d.isnot(None)) & (i_d > e_d),
            )
        )
        # [end]

        rows = query.all()
        phrases = []

        for (full_name, terms) in rows:
            if not isinstance(terms, list):
                terms = []

            for text in terms:
                phrase = Phrase(
                    phrase=text,
                    source=ESearchSource.LIST_INAGENTS,
                    phrase_original=full_name
                )

                phrases.append(phrase)

        return phrases
