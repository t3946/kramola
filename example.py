from docx import Document
from copy import deepcopy

from docx.enum.text import WD_COLOR_INDEX


def remove_run(run):
    parent = run._element.getparent()
    parent.remove(run._element)


doc = Document("1.docx")
paragraph = doc.paragraphs[0]  # Первый параграф
run = paragraph.runs[1]        # Первый run в этом параграфе


# Клонируем XML элемента run
new_run_element = deepcopy(run._element)

# Вставляем клон сразу после исходного run
run._element.addnext(new_run_element)
remove_run(run)



# дальше каким то образом найти новый run и подсветить его
new_run = paragraph.runs[1]
new_run.font.highlight_color = WD_COLOR_INDEX.BRIGHT_GREEN



# Сохраняем новый документ
doc.save("result.docx")