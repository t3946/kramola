import docx

from services.analyser import Analyser, AnalyseData


filename = 'main.docx'
source_path = f"./tests/test-xml/input.docx"
doc = docx.Document(source_path)

analyse_data = AnalyseData()
analyse_data.readFromList({'apple', 'яблоко'})

analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse_and_highlight_xml()

destination_path = f"./results/{filename}"
doc.save(destination_path)
