from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from services.utils.timeit import timeit

@timeit
def highlight_word(doc_path, target_word, save_path, highlight_color=WD_COLOR_INDEX.YELLOW):
    doc = Document(doc_path)
    changed = False

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if run.text == target_word:
                try:
                    run.font.highlight_color = highlight_color
                    changed = True
                except Exception:
                    pass

    if changed:
        doc.save(save_path)
        print(f'Слово "{target_word}" успешно выделено')
    else:
        print(f'Слово "{target_word}" не найдено')
