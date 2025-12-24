from typing import List, Dict
from services.document_service import extract_lines_from_docx
from services.fulltext_search.fulltext_search import FulltextSearch
from services.fulltext_search.token import Token


class AnalysisData:
    tokens: Dict[str, List[Token]]

    def __init__(self, terms = None):
        self.tokens = {}

        if terms is not None:
            self.read_from_list(terms)

    def read_from_list(self, terms: List[str]):
        for term in terms:
            if term and term.strip():
                text = term.strip()
                self.tokens[text] = FulltextSearch.tokenize_text(text)

    def read_from_docx(self, path):
        terms = extract_lines_from_docx(path)
        self.read_from_list(terms)
