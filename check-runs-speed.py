from docx import Document
from utils.timeit import timeit


@timeit
def main():
    doc = Document("./tests/170000 words.docx")
    paragraphs = doc.paragraphs

    runs_generated = 0

    for i in range(0, 10):
        for paragraph in paragraphs:
            runs_generated += len(paragraph.runs)

    print(runs_generated)

main()