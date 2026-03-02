import re
from typing import Union

from services.parser_feds_fm.process_raw import ProcessRaw


class ProcessRawInternational(ProcessRaw):
    @staticmethod
    def _parse_international_fl_name(raw):
        names = {"main": ""}
        raw = ProcessRaw._strip_number(raw)
        names["main"] = raw.split(",", 1)[0]

        return names

    @staticmethod
    def _parse_international_ul_name(raw):
        names = {
            "main": "",
            "additional": []
        }
        raw = ProcessRaw._strip_number(raw)
        name_part = raw.split(",", 1)[0]
        # name with shortcut like "Apple Inc. (AI)", will found ["Apple Inc.", "AI"]
        matches = re.match(r'(.+?)\s*\((.+?)\)', name_part)

        if matches:
            names["main"] = matches[1].strip()
            names["additional"] = [matches[2]]
        else:
            names["main"] = name_part

        return names

    @staticmethod
    def _parse_sanction_code(text) -> Union[str, None]:
        """
        extract sanction code from text and return None if no sanction code(ex. QDi.289, TAi.155, IRi.001, QDi.1234)
        """
        pattern = r'(?!код\s+санкций\s+ООН:\s+)(\w+?\.\d+)'
        match = re.search(pattern, text, re.IGNORECASE)

        return match.group(0) if match else None