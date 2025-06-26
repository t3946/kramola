from typing import Any

class DocxCache:
    def __init__(self, document):
        self.document = document
        self.documentStyles = document.styles
        self.styleCache: dict[str, any] = {}

    def getStyle(self, name: str) -> Any:
        # define if no style
        if (name not in self.styleCache) :
            self.styleCache[name] = self.documentStyles[name]

        return self.styleCache[name]
