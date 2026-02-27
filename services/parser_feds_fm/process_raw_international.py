import re
from typing import Union


class ProcessRawInternational:
    @staticmethod
    def _parse_sanction_code(text) -> Union[str, None]:
        """
        extract sanction code from text and return None if no sanction code(ex. QDi.289, TAi.155, IRi.001, QDi.1234)
        """
        pattern = r'(?!код\s+санкций\s+ООН:\s+)(\w+?\.\d+)'
        match = re.search(pattern, text, re.IGNORECASE)

        return match.group(0) if match else None