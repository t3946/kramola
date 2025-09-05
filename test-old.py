from services.analyser import Analyser
from services.highlight_service import analyze_and_highlight_docx
from services.pymorphy_service import prepare_search_terms, get_highlight_search_data
from services.solution import highlight_word

terms = {'apple', 'яблоко'}
prepared_data_unified = prepare_search_terms(terms)
search_data_for_highlight = get_highlight_search_data(prepared_data_unified)

source_path = "./tests/functionality/main.docx"
search_phrase_lemmas_map = {}
output_path = "./results/output.docx"
# Использование:

analyze_and_highlight_docx(source_path, search_data_for_highlight, search_phrase_lemmas_map, output_path)

# 100 words       ~  0.27s
# 1000 words      ~  2.40s
# 1000 words 10 p ~  2.20s
# 2000 words      ~  4.80s
# 4000 words      ~    11s
# 4000 words 1 p  ~     8s
# 10000 words     ~    26s
# 170000 words    ~   476s 1ЛДРедJones,_The_Fall_of_Robespierre

# новая функция в разы быстрее
# highlight_word('./tests/1000 words.docx', 'word', './results/output.docx')

# изначально 1000 words Обрабатывался за 6.5s, вдобавок была квадратичная сложности, что не позволяло обработать крупный файл вовсе
# по оптимизации есть две идеи, переделать сборку файла ответа на "скопировал, подправвил", и C#