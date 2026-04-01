from typing import Optional, Tuple

from petrovich.enums import Gender


class PersonName:
    surname: str
    firstname: str
    patronimic: str
    gender: Optional[str]

    def __init__(self, full_name, gender: Optional[str] = None):
        self.surname, self.firstname, self.patronimic = self._split_full_name(full_name)

        if None in (self.surname, self.firstname, self.patronimic):
            raise ValueError("Unsupported full name format")

        self.gender = gender or self.detect_gender()

    def detect_gender(self) -> Optional[str]:
        # [start] try to detect by patronimic
        patronymic = self.patronimic

        # Отчество — главный индикатор
        if patronymic.endswith(('евич', 'ич', 'ыч')):
            return Gender.MALE
        elif patronymic.endswith(('евна', 'овна', 'евна', 'инична')):
            return Gender.FEMALE
        # [end]

        # [start] try to detect by firstname
        firstname = self.firstname
        male_endings = ('ий', 'ов', 'ев', 'ир')
        female_endings = ('а', 'я')

        if any(firstname.endswith(end) for end in male_endings):
            return Gender.MALE
        elif any(firstname.endswith(end) for end in female_endings):
            return Gender.FEMALE
        # [end]

        return None

    @staticmethod
    def _split_full_name(full_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        parts: list[str] = full_name.strip().split()

        if len(parts) != 3:
            return None, None, None

        return parts[0], parts[1], parts[2]
