from enum import Enum


class WordsFormat(Enum):
    DOCX = ".docx"
    XLSX = ".xlsx"
    TXT = ".txt"

    @classmethod
    def extensions(cls) -> tuple[str, ...]:
        return tuple(f.value for f in cls)
