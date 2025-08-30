import docx

from services.analyser import Analyser, AnalyseData

source_path = "./tests/100 words.docx"
doc = docx.Document(source_path)
analyse_data = AnalyseData({'word'}, {'word'})
analyser = Analyser(doc)
analyser.set_analyse_data(analyse_data)
analyser.analyse()
