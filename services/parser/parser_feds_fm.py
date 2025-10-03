from typing import List

from numpy.ma.core import append

from services.loader_selenium import LoaderSelenium
import re

class ParserFedsFM:
    def __init__(self):
        self.loader = LoaderSelenium()

    def load(self):
        try :
            self.loader.get("https://www.fedsfm.ru/documents/terrorists-catalog-portal-act")
            elements = self.loader.find_elements("ol.terrorist-list li")[:10]
            texts = [el.text for el in elements]
            pattern = re.compile(r'\d+\.\s+([А-ЯЁ\s]+)[\*,]')
            namesFL: List[str] = []

            for text in texts:
                namesFL.append(pattern.findall(text)[0])

            return {
                "namesFL": namesFL,
            }
        finally:
            self.loader.driver.quit()