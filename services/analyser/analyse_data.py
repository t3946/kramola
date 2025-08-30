class AnalyseData:
    lemmas: list[str]
    stems: list[str]

    def __init__(self, lemmas, stems):
        self.lemmas = lemmas
        self.stems = stems