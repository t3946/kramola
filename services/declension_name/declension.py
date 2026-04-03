import os
import sys
from typing import Optional

from petrovich.enums import Case, Gender
from petrovich.main import Petrovich

from services.declension_name.person_name import PersonName

# fix windows encoding
if not sys.flags.utf8_mode:
    os.execv(sys.executable, [sys.executable, "-X", "utf8", *sys.argv])


class Declension:
    def __init__(self) -> None:
        self._petrovich: Petrovich = Petrovich()

    def decline_full_name(
        self,
        full_name: str,
        gender: Optional[str] = None
    ) -> list[str]:
        result = [full_name]

        try:
            person_name = PersonName(full_name, gender)
        except ValueError as e:
            return result

        gender = person_name.gender or Gender.MALE
        cases = [Case.GENITIVE, Case.DATIVE, Case.ACCUSATIVE, Case.INSTRUMENTAL, Case.PREPOSITIONAL]

        for case in cases:
            d_surname: str = self._petrovich.lastname(person_name.surname, case=case, gender=gender)
            d_firstname: str = self._petrovich.firstname(person_name.firstname, case=case, gender=gender)
            d_patronimic: str = self._petrovich.middlename(person_name.patronimic, case=case, gender=gender)
            result.append(f"{d_surname} {d_firstname} {d_patronimic}")

        return result
