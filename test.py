import docx

from services.analyser import AnalyserDocx, AnalyseData

def russian_history():
    source_path = f"./notes/tests/russian-history/История древней Руси.docx"
    doc = docx.Document(source_path)

    analyse_data = AnalyseData()
    analyse_data.read_from_docx(f"./notes/tests/russian-history/Слова.docx")

    analyser = AnalyserDocx(doc)
    analyser.set_analyse_data(analyse_data)
    analyser.analyse_and_highlight()

    destination_path = f"./notes/tests/russian-history/output.docx"
    doc.save(destination_path)


def the_fall_of_robespierre():
    source_path = f"./notes/tests/the-fall-of-robespierre/source.docx"
    doc = docx.Document(source_path)

    analyse_data = AnalyseData()
    analyse_data.read_from_docx(f"./notes/tests/the-fall-of-robespierre/words.docx")

    analyser = AnalyserDocx(doc)
    analyser.set_analyse_data(analyse_data)
    analyser.analyse_and_highlight()

    destination_path = f"./notes/tests/the-fall-of-robespierre/output.docx"
    doc.save(destination_path)

the_fall_of_robespierre()
