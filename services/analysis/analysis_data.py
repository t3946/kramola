from typing import List, Optional, Dict
from services.document_service import extract_lines_from_docx
from services.fulltext_search.phrase import Phrase
from services.words_list.list_persons import ListPersons
from services.words_list.list_companies import ListCompanies
from services.words_list import PredefinedListKey


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

    def load_predefined_lists(self, list_keys: List[str]) -> None:
        """Load ready-made Phrase objects from Redis lists by their keys."""
        list_mapping = {
            PredefinedListKey.FOREIGN_AGENTS_PERSONS: ListPersons,
            PredefinedListKey.FOREIGN_AGENTS_COMPANIES: ListCompanies
        }

        for key in list_keys:
            # Convert string key to enum if needed
            key_enum = PredefinedListKey(key) if isinstance(key, str) else key
            
            if key_enum in list_mapping:
                words_list = list_mapping[key_enum]()
                phrases = words_list.load()

                for phrase in phrases:
                    if phrase and phrase.phrase and phrase.phrase.strip():
                        text = phrase.phrase.strip()

                        if text not in self.phrases:
                            self.phrases[text] = phrase

    def read_from_docx(self, path: str) -> None:
        terms = extract_lines_from_docx(path)
        self.read_from_list(terms)
