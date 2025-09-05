import docx
from typing import List

from docx.enum.text import WD_COLOR_INDEX
from docx.text.paragraph import Paragraph
from services.analyser import AnalyseData
from services.common_docx import tokenize_paragraph_universal
from services.highlight_service import _find_matches_in_paragraph_tokens
from utils.timeit import timeit


class Analyser:
    document: docx.Document
    analyse_data: AnalyseData

    def __init__(self, document):
        self.document = document

    def set_analyse_data(self, analyse_data):
        self.analyse_data = analyse_data

    def find_source_run(self, char_idx_in_para):
        print('find_source_run')
        # for start, end, run_obj in run_char_positions:
        #     if start <= char_idx_in_para < end: return run_obj
        # return source_runs[-1] if source_runs else None

    @timeit
    def analyse_and_highlight(self):
        paragraphs: List[Paragraph] = self.document.paragraphs

        for paragraph in paragraphs:
            # [start] save run positions
            source_runs = list(paragraph.runs)
            current_char_pos = 0
            run_char_positions = []

            for run in source_runs:
                run_len = len(run.text)
                run_char_positions.append((current_char_pos, current_char_pos + run_len, run))
                current_char_pos += run_len

            def find_source_run(char_idx_in_para):
                for start, end, run_obj in run_char_positions:
                    if start <= char_idx_in_para < end: return run_obj
                return source_runs[-1] if source_runs else None
            # [end]

            tokens = tokenize_paragraph_universal(paragraph)

            matches = _find_matches_in_paragraph_tokens(
                tokens,
                self.analyse_data.lemmas,
                self.analyse_data.stems,
                {}
            )

            for match in matches:
                start_token_idx = match['start_token_idx']
                end_token_idx = match['end_token_idx']

                for i in range(start_token_idx, end_token_idx + 1):
                    token = tokens[i]
                    run = find_source_run(token['start'])
                    run.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN