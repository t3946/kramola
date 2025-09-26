import docx

from services.analyser import Analyser, AnalyseData

filename = 'main.docx'
source_path = f"./notes/tests/100000 words.docx"
doc = docx.Document(source_path)

analyse_data = AnalyseData()
analyse_data.readFromList({'apple', 'яблоко'})

analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse_and_highlight()

destination_path = f"./notes/tests/test-xml/output.docx"
doc.save(destination_path)
