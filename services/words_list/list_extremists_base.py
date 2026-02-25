from abc import ABC
from typing import ClassVar, List, Optional

from models import ExtremistTerrorist
from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from services.enum import WordsListKey
from services.fulltext_search.phrase import Phrase


class ListExtremistsTerroristsBase(ABC):
    """Base for loading extremists/terrorists search_terms from DB by area and status."""

    key = WordsListKey.EXTREMISTS_TERRORISTS
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
                    source_list=self,
                    phrase_original=full_name
                )
                phrases.append(phrase)

        return phrases
