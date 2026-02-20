from abc import ABC
from typing import ClassVar, List, Optional

from models import ExtremistTerrorist
from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from services.enum.predefined_list import ESearchSource
from services.fulltext_search.phrase import Phrase
from services.words_list.list_colors import ListColor


class ListExtremistsTerroristsBase(ABC, ListColor):
    """Base for loading extremists/terrorists search_terms from DB by area and status."""

    key = "extremists_terrorists"
    area: ClassVar[Optional[ExtremistArea]] = None
    status: ClassVar[Optional[ExtremistStatus]] = None

    def __init__(self) -> None:
        super().__init__()

    def load(self) -> list[Phrase]:
        query = ExtremistTerrorist.query.with_entities(
            ExtremistTerrorist.full_name,
            ExtremistTerrorist.search_terms
        )
        if self.area is not None:
            query = query.filter(ExtremistTerrorist.area == self.area.value)
        if self.status is not None:
            query = query.filter(ExtremistTerrorist.type == self.status.value)
        rows = query.all()
        phrases: list[Phrase] = []

        for (full_name, terms) in rows:
            if not isinstance(terms, list):
                terms = []

            for text in terms:
                phrase = Phrase(
                    phrase=text,
                    source=ESearchSource.LIST_EXTREMISTS_TERRORISTS,
                    phrase_original=full_name
                )
                phrases.append(phrase)

        return phrases
