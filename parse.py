from services.parser.parser_feds_fm import ParserFedsFM
from services.words_list.list_companies import ListCompanies
from services.words_list.list_persons import ListPersons

parser = ParserFedsFM()
data = parser.load()

lp = ListPersons()
lp.save(data['namesFL'])

lc = ListCompanies()
lc.save(data['namesUL'])

lc = ListCompanies()
print(lc.load())