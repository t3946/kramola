from abc import ABC

class WordsList(ABC):
    key: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
