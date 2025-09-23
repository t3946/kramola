# from docx import Document
# from copy import deepcopy
# from docx.oxml import OxmlElement
# from docx.oxml.ns import qn
#
#
# def split_run_xml(paragraph, run_element, split_pos):
#     # Получаем текст внутри w:t
#     text_element = run_element.find(qn('w:t'))
#     if text_element is None:
#         return
#
#     text = text_element.text
#     if not text or split_pos <= 0 or split_pos >= len(text):
#         return  # Неправильный индекс или пустой текст
#
#     # Разбиваем текст
#     part1 = text[:split_pos]
#     part2 = text[split_pos:]
#
#     # Меняем текст текущего run
#     # text_element.text = part1
#
#     # Клонируем run (w:r) элемент включая все вложенные свойства
#     new_run = OxmlElement('w:r')
#     for child in run_element:
#         new_run.append(deepcopy(child))
#
#     # Меняем текст в клоне на вторую часть
#     new_text_element = new_run.find(qn('w:t'))
#     new_text_element.text = part2
#
#     # Вставляем новый run после оригинала
#     run_element.addnext(new_run)
#
#
# def test_clone_run():
#     doc = Document('notes/tests/test-xml/input.docx')
#
#     # Получаем XML-элементы run из первого абзаца (без использования runs API)
#     first_para = doc.paragraphs[0]
#     runs_xml = first_para._element.findall(qn('w:r'))
#
#     # Разбиваем первый run напрямую на XML уровне
#     if runs_xml:
#         split_run_xml(first_para, runs_xml[0], 5)
#
#     doc.save('notes/tests/test-xml/output.docx')
#
#
# def test_p_for():
#     doc = Document('notes/tests/История древней Руси.docx')
#
#     for para in doc.paragraphs:
#         p_element = para._element
#
#         for child in p_element:
#             if child.tag == qn('w:r'):
#                 # print("run: \"\"")
#                 wts = len(child.findall(qn('w:t')))
#
#                 if wts != 1:
#                     print('strange run: ', wts)
#
#             # elif child.tag == qn('w:hyperlink'):
#             #     print("Это гиперссылка:", child)
#
#
# test_p_for()


import docx

from services.analyser import Analyser, AnalyseData


filename = 'main.docx'
source_path = f"./notes/tests/test-xml/input.docx"
doc = docx.Document(source_path)

analyse_data = AnalyseData()
analyse_data.readFromList({'apple', 'яблоко'})

analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse_and_highlight_xml()

destination_path = f"./notes/tests/test-xml/output.docx"
doc.save(destination_path)
