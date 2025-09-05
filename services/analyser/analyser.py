import docx
from typing import List

from docx.enum.text import WD_COLOR_INDEX
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from services.analyser import AnalyseData
from services.common_docx import tokenize_paragraph_universal
from services.highlight_service import _find_matches_in_paragraph_tokens
from utils.timeit import timeit
from copy import deepcopy


class Analyser:
    document: docx.Document
    analyse_data: AnalyseData

    def __init__(self, document):
        self.document = document

    def set_analyse_data(self, analyse_data):
        self.analyse_data = analyse_data

    @staticmethod
    def find_run_by_char_index(paragraph, char_index) -> tuple[Run, int, int, int]:
        runs = paragraph.runs
        start_index = 0
        run_index = 0

        for run in runs:
            end_index = start_index + len(run.text) - 1

            if start_index <= char_index <= end_index:
                return run, start_index, end_index, run_index

            start_index = end_index + 1
            run_index += 1

    # find and split run on three new: before, middle and after parts where middle arranged with supplied indices
    @staticmethod
    def isolate_new_run(paragraph, phrase_start_index, phrase_end_index) -> Run:
        # find target run
        target_run, run_start_index, run_end_index, target_run_index = Analyser.find_run_by_char_index(paragraph, phrase_start_index)

        # calculate phrase destination in target run
        phrase_relative_start_index = phrase_start_index - run_start_index
        phrase_relative_end_index = phrase_end_index - run_start_index

        # [start] split target run on three parts
        # clone target run
        all_text = target_run.text
        text_before = all_text[0:phrase_relative_start_index]
        text_phrase = all_text[phrase_relative_start_index:phrase_relative_end_index]
        text_after = all_text[phrase_relative_end_index:len(all_text)]

        target_run.text = text_after
        new_run_element = deepcopy(target_run._element)
        target_run._element.addnext(new_run_element)

        target_run.text = text_phrase
        new_run_element = deepcopy(target_run._element)
        target_run._element.addnext(new_run_element)

        target_run.text = text_before
        new_run_element = deepcopy(target_run._element)
        target_run._element.addnext(new_run_element)
        # [end]

        # remove old run
        parent = target_run._element.getparent()
        parent.remove(target_run._element)

        return paragraph.runs[target_run_index + 1]

    @timeit
    def analyse_and_highlight(self):
        paragraphs: List[Paragraph] = self.document.paragraphs

        for paragraph in paragraphs:
            source_runs = list(paragraph.runs)
            current_char_pos = 0
            run_char_positions = []

            for run in source_runs:
                run_len = len(run.text)
                run_char_positions.append((current_char_pos, current_char_pos + run_len, run))
                current_char_pos += run_len

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
                    phrase_run = self.isolate_new_run(paragraph, token['start'], token['end'])
                    phrase_run.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN
