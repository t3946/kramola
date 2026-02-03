FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libtesseract-dev \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python3 -m nltk.downloader -d /usr/share/nltk_data wordnet omw-1.4
ENV NLTK_DATA=/usr/share/nltk_data

COPY . /app

RUN mkdir -p /app/uploads /app/results /app/predefined_lists /app/models \
    /app/uploads/highlight /app/results/highlight \
    /app/uploads/footnotes /app/results/footnotes

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "4", "app:app"]
CMD [ \
    "gunicorn", \
    "--bind", "0.0.0.0:5000", \
    "--worker-class", "eventlet", \
    "--workers", "1", \
    "--log-level", "debug", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--timeout", "1800", \
    "--reload", \
    "app:socketio" \
]