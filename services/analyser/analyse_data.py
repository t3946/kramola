from services.document_service import extract_lines_from_docx
from services.pymorphy_service import prepare_search_terms, get_highlight_search_data


class AnalyseData:
    lemmas: list[str]
    stems: list[str]

    def __init__(self, terms = None):
        if terms is not None:
            self.readFromList(terms)

    def readFromList(self, terms):
        prepared_data_unified = prepare_search_terms(terms)
        search_data_for_highlight = get_highlight_search_data(prepared_data_unified)

        self.lemmas = search_data_for_highlight.get('lemmas')
        self.stems = search_data_for_highlight.get('stems')

    def readFromDocx(self, path):
        terms = extract_lines_from_docx(path)
        self.readFromList(terms)
