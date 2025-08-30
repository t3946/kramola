import docx
from services.analyser import AnalyseData
from services.common_docx import tokenize_paragraph_universal
from services.highlight_service import _find_matches_in_paragraph_tokens

class Analyser:
    document: docx.Document
    analyse_data: AnalyseData

    def __init__(self, document):
        self.document = document

    def set_analyse_data(self, analyse_data):
        self.analyse_data = analyse_data

    def analyse(self):
        paragraphs = self.document.paragraphs

        for paragraph in paragraphs:
            tokens = tokenize_paragraph_universal(paragraph)

            matches = _find_matches_in_paragraph_tokens(
                tokens,
                self.analyse_data.lemmas,
                self.analyse_data.stems,
                {}
            )

            print(matches)