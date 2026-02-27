import re
from typing import Union
from datetime import date


class ProcessRawRussian:
    @staticmethod
    def _parse_birthdate(value: Union[str, None]) -> Union[date, None]:
        # parse birthdate in format: DD.MM.YYYY г.р.
        if not value:
            return None

        pattern = r'(\d{2})\.(\d{2})\.(\d{4})\s*г\.р\.'
        match = re.search(pattern, value)

        if not match:
            return None

        day, month, year = map(int, match.groups())

        return date(year, month, day)
