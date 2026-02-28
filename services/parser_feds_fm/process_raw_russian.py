import re
from typing import Union
from datetime import date


class ProcessRawRussian:
    @staticmethod
    def _parse_birthdate(raw: str) -> Union[date, None]:
        # parse birthdate in format: DD.MM.YYYY г.р.
        if not raw:
            return None

        pattern = r'(\d{2})\.(\d{2})\.(\d{4})\s*г\.р\.'
        match = re.search(pattern, raw)

        if not match:
            return None

        day, month, year = map(int, match.groups())

        return date(year, month, day)

    @staticmethod
    def _parse_ru_fl_name(raw: str) -> dict:
        names = {"main": "", "additional": []}

        # [start] process number
        raw = raw.strip()
        m_num = re.match(r"^\s*\d+\.\s*", raw)
        raw = raw[m_num.end():]
        # [end]

        # [start] process main name
        # asterisk marks end of first name
        if "*" in raw:
            main, rest = raw.split("*", 1)
            names["main"] = main.strip()
            raw = rest
        else:
            idx = raw.find(",")
            names["main"] = raw[:idx].strip()
            raw = raw[idx + 1:]
        # [end]

        # [start] process additional names
        matches = re.search(r"^[ ,]*\((.+?)\)", raw)

        if matches:
            additional_raw = re.search(r"^[ ,]*\((.+?)\)", raw)[1]

            if additional_raw:
                names["additional"] = [name.strip() for name in additional_raw.split(';')]
        # [end]

        return names

    def _parse_ru_ul_name(raw: str) -> dict:
        pass