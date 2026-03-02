import re

class ProcessRaw:
    @staticmethod
    def _strip_number(raw: str) -> str:
        raw = raw.strip()
        m_num = re.match(r"^\s*\d+\.\s*", raw)
        raw_without_number = raw[m_num.end():]

        return raw_without_number
