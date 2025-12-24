from typing import List, Optional, Dict
from services.document_service import extract_lines_from_docx
from services.fulltext_search.phrase import Phrase


class AnalysisData:
    phrases: Dict[str, Phrase]

    def __init__(self, terms: Optional[List[str]] = None) -> None:
        self.phrases = {}

        if terms is not None:
            self.read_from_list(terms)

    def read_from_list(self, terms: List[str]) -> None:
        for term in terms:
            if term and term.strip():
                text = term.strip()

                if text not in self.phrases:
                    self.phrases[text] = Phrase(text)

    def read_from_docx(self, path: str) -> None:
        terms = extract_lines_from_docx(path)
        self.read_from_list(terms)
