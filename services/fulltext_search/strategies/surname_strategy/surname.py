from services.fulltext_search.utils import normalize_text

from .declension import (
    EXCEPTION_FORMS,
    decline_surname_forms,
)

PADEZHI: tuple[str, ...] = ("nom", "gen", "dat", "acc", "ins", "pre")


class Surname:
    """Nominative-base surname: precomputed declension surfaces for check()."""
    surname: str

    def __init__(self, surname: str) -> None:
        stripped: str = surname.strip()
        self.surname: str = stripped
        normalized_key: str = normalize_text(stripped)

        self.is_dictionary_exception: bool = normalized_key in EXCEPTION_FORMS
        self._normalized_forms: frozenset[str] = self._build_normalized_forms()

        self.is_indeclinable: bool = len(self._normalized_forms) == 1

    def _build_normalized_forms(self) -> frozenset[str]:
        """
        Returns a frozenset of normalized strings: all word forms of this surname
        (all cases, both genders). check(source) is True iff normalize(source) is in this set.
        All strings are lowercased, Ё→Е, trimmed.
        """
        acc: set[str] = set()
        genders: tuple[str, ...] = ("male", "female")

        for g in genders:
            paradigm: dict[str, list[str]] = decline_surname_forms(
                self.surname,
                g,
                {},
            )

            for case in PADEZHI:
                surfaces: list[str] = paradigm[case]

                for surface in surfaces:
                    acc.add(normalize_text(surface))

        return frozenset(acc)

    def check(self, source: str) -> bool:
        normalized_source: str = normalize_text(source)

        return normalized_source in self._normalized_forms
