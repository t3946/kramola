import docx

from services.analyser import Analyser, AnalyseData

filename = 'main.docx'
source_path = f"./tests/functionality/{filename}"
doc = docx.Document(source_path)
analyse_data = AnalyseData({'apple'}, {'apple'})
analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse_and_highlight()

destination_path = f"./results/{filename}"
doc.save(destination_path)
