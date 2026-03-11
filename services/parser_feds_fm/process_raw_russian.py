import re
from typing import Union
from datetime import date

from services.parser_feds_fm.process_raw import ProcessRaw


class ProcessRawRussian(ProcessRaw):
    @staticmethod
    def _parse_birth_details(raw: str) -> Union[dict, None]:
        result = {
            "date": None,
            "place": None
        }
        # parse birthdate in format: DD.MM.YYYY г.р.
        if not raw:
            return result

        # [start] parse birthdate
        match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s*г\.р\.', raw)

        if not match:
            return result

        day, month, year = map(int, match.groups())
        result["date"] = date(year, month, day)
        # [end]

        # [start] birthplace
        match = re.search(r'(?:\d{2}\.\d{2}\.\d{4}\s*г\.р\.)[\s,]+([\w.\s]+)', raw)
        result["place"] = match[1] if match else None
        # [end]

        return result

    @staticmethod
    def _extract_surname(name: str) -> str:
        return name.strip().split(' ')[0]

    @staticmethod
    def _parse_ru_fl_name(raw: str) -> dict:
        names = {"main": "", "additional": []}

        raw = ProcessRaw._strip_number(raw)

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

    @staticmethod
    def _parse_ru_ul_name(raw: str) -> dict:
        is_name_found = False
        names = {
            "main": "",
            "additional": [],
            "parsing_problem": False
        }

        raw = ProcessRaw._strip_number(raw)

        simple_pattern_1 = r"^([\s\w\-`]+)[\s*,;]+$"

        # [start] find main name
        if re.search(simple_pattern_1, raw):
            names["main"] = re.search(simple_pattern_1, raw)[1].strip()
        elif "*" in raw:
            names["main"] = raw.split("*", 1)[0].strip()
            is_name_found = True
        elif "(" in raw:
            matches = re.search(r"^[\s\w\-`]+", raw)

            if matches:
                names["main"] = matches[0].strip()
                is_name_found = True
        # [end]

        # [start] find additional name
        if is_name_found:
            matches = re.search(r"\((.*?)\),", raw)

            if matches:
                match = matches[1]
                names["additional"] = [name.strip() for name in match.split(';')]
        # [end]

        names["parsing_problem"] = not is_name_found

        return names
