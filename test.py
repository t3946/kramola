import docx

from services.analyser import Analyser, AnalyseData

filename = '1 words.docx'
source_path = f"./tests/{filename}"
doc = docx.Document(source_path)
analyse_data = AnalyseData({'word'}, {'word'})
analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse_and_highlight()

destination_path = f"./results/{filename}"
doc.save(destination_path)
