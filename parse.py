# from services.parser.parser_feds_fm import ParserFedsFM
# from services.words_list.list_companies import ListCompanies
# from services.words_list.list_persons import ListPersons
#
# parser = ParserFedsFM()
# data = parser.load()
#
# lp = ListPersons()
# lp.save(data['namesFL'])
#
# lc = ListCompanies()
# lc.save(data['namesUL'])
#
# lc = ListCompanies()
# print(lc.load())

persons_words = ['A B C']
surnames = set()

for person in persons_words:
    # Проверяем, что это строка
    if not isinstance(person, str):
        continue
    person_clean = person.strip()
    if not person_clean:
        continue
    # Разделяем по пробелам
    parts = person_clean.split()
    # Проверяем, что это похоже на ФИО (минимум 2 слова)
    if len(parts) >= 2:
        surname = parts[0].strip()
        if surname:
            surnames.add(surname)

print(surnames)