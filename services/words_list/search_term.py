from enum import Enum

class EType(Enum):
    TEXT = 'text'
    SURNAME = 'surname'

class SearchTerm:
    type: EType
    text: str

    def __init__(self, text: str, term_type: EType = EType.TEXT):
        self.text = text
        self.type = term_type
