from enum import Enum


class SourceFormat(Enum):
    DOCX = ".docx"
    DOC = ".doc"
    PDF = ".pdf"
    ODT = ".odt"

    @classmethod
    def extensions(cls) -> tuple[str, ...]:
        return tuple(f.value for f in cls)
