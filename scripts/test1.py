import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.analyser.fulltext_search import FulltextSearch


# 17. Местная организация города Краснодара – «Пит Буль» («Pit Bull»)
#    И.п. Местная организация города Краснодара – «Пит Буль» («Pit Bull»)
#    Р.п. Местной организации города Краснодара – «Пит Буля» («Pit Bull»)
#    Д.п. Местной организации города Краснодара – «Пит Булю» («Pit Bull»)
#    В.п. Местную организацию города Краснодара – «Пит Буль» («Pit Bull»)
#    Т.п. Местной организацией города Краснодара – «Пит Булем» («Pit Bull»)
#    П.п. о Местной организации города Краснодара – «Пит Буле» («Pit Bull»)


phrase = "яблоки"

tokens = FulltextSearch.tokenize_text(phrase)

for token in tokens:
    if token['type'] == 'word':
        print(f"Слово: {token['text']}")
        print(f"  Лемма: {token['lemma']}")
        print(f"  Стемма: {token['stem']}")
        print()