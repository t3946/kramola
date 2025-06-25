# --- START OF FILE app.py ---
import os
import time
import traceback
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler # <-- Используем этот хендлер
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
from flask_executor import Executor 
import uuid 
import redis
from services.document_service import save_uploaded_file, extract_lines_from_docx, TOKEN_PATTERN
from services.pymorphy_service import (

    load_pymorphy,
    load_nltk_lemmatizer,
    get_morph_analyzer,

)
from services.highlight_service import analyze_and_highlight_docx, analyze_and_highlight_pdf # Добавляем PDF обработчик

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')
# Устанавливаем DEBUG уровень, как было в исходном запросе
log_level = logging.DEBUG

log_file = "log/app.log" # Имя основного лог-файла
log_dir = os.path.dirname(log_file)
# Проверяем и создаем директорию для логов
if log_dir and not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except OSError as e:
         # Выводим ошибку в stderr, так как логгер еще может быть не готов
        print(f"CRITICAL ERROR: Could not create log directory '{log_dir}'. Error: {e}")
        # Можно использовать fallback имя файла или выйти
        log_file = "fallback_app.log"

file_handler = ConcurrentRotatingFileHandler(
    log_file,
    maxBytes=1024 * 1024 * 5, # 5 MB
    backupCount=2,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(log_level)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
stream_handler.setLevel(log_level)

# Настраиваем корневой логгер
root_logger = logging.getLogger()
if root_logger.hasHandlers():
    root_logger.handlers.clear()
root_logger.setLevel(log_level) # Устанавливаем минимальный уровень для корневого логгера
root_logger.addHandler(file_handler) # Добавляем файловый хендлер
root_logger.addHandler(stream_handler) # Добавляем консольный хендлер


# Конфигурация Redis (можно вынести в app.config)
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB_TASKS', 0)) # Отдельная БД для задач



# Уменьшаем уровень логирования для "шумных" библиотек
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("nltk").setLevel(logging.INFO)
logging.getLogger("pymorphy3").setLevel(logging.INFO)
logging.getLogger("PIL").setLevel(logging.INFO) # Pillow может быть шумным
logging.getLogger("concurrent_log_handler").setLevel(logging.WARNING) # Логи самого хендлера

app = Flask(__name__)
app.logger.name = 'Flask_App' # Присваиваем имя логгеру Flask после создания app

app.secret_key = os.environ.get('FLASK_SECRET_KEY', b'\xa2\\"Rr\x91\xc5>e\xbc\xc5\x86\xb2O\x15\x04Yao\x81\xe9\x90\xac\xec')

app.config['EXECUTOR_TYPE'] = 'thread'  # или 'process'
app.config['EXECUTOR_MAX_WORKERS'] = 5 # Количество одновременных фоновых задач
executor = Executor(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Общие директории
app.config['UPLOAD_DIR'] = os.path.join(BASE_DIR, "uploads")
app.config['RESULT_DIR'] = os.path.join(BASE_DIR, "results")
app.config['PREDEFINED_LISTS_DIR'] = os.path.join(BASE_DIR, "predefined_lists")

# Опциональные отдельные директории для инструментов
app.config['UPLOAD_DIR_HIGHLIGHT'] = os.path.join(BASE_DIR, "uploads", "highlight")
app.config['RESULT_DIR_HIGHLIGHT'] = os.path.join(BASE_DIR, "results", "highlight")
app.config['UPLOAD_DIR_FOOTNOTES'] = os.path.join(BASE_DIR, "uploads", "footnotes")
app.config['RESULT_DIR_FOOTNOTES'] = os.path.join(BASE_DIR, "results", "footnotes")


try:
    # Создаем пул соединений для эффективности
    redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    # decode_responses=True чтобы ключи и значения были строками, а не байтами
    app.redis_client_tasks = redis.Redis(connection_pool=redis_pool)
    app.redis_client_tasks.ping() # Проверяем соединение
    app.logger.info(f"Successfully connected to Redis for task storage at {REDIS_HOST}:{REDIS_PORT}, DB: {REDIS_DB}")
except redis.exceptions.ConnectionError as e:
    app.logger.error(f"Could not connect to Redis for task storage: {e}. Task status persistence will not work.")
    app.redis_client_tasks = None 
except Exception as e_general: 
    app.logger.error(f"An unexpected error occurred during Redis client initialization: {e_general}. Task status persistence will not work.")
    app.redis_client_tasks = None



# Формат: 'ключ_файла_без_расширения': 'Отображаемое имя в UI'
app.config['PREDEFINED_LISTS'] = {
    "mat": "Матные слова",
    "narkot" : "Запрещенные вещества",
    "yaldo" : "Ругательства",
    "ino" : "Инагенты (ФИО)",
    "inu_b" : "Инагенты (Организации)"

}



# --- Создание директорий при старте ---
# Создаем базовые и специфичные директории, если они не существуют
dirs_to_create = [
    app.config['UPLOAD_DIR'],
    app.config['RESULT_DIR'],
    app.config['PREDEFINED_LISTS_DIR'],
    app.config['UPLOAD_DIR_HIGHLIGHT'],
    app.config['RESULT_DIR_HIGHLIGHT'],
    app.config['UPLOAD_DIR_FOOTNOTES'],
    app.config['RESULT_DIR_FOOTNOTES']
]
for dir_path in dirs_to_create:
    try:
        os.makedirs(dir_path, exist_ok=True)
        # Используем логгер app после его настройки
        app.logger.debug(f"Directory checked/created: {dir_path}")
    except OSError as e:
        app.logger.error(f"Failed to create directory {dir_path}: {e}")

app.logger.info(f"Base directories configured: UPLOAD={app.config['UPLOAD_DIR']}, RESULT={app.config['RESULT_DIR']}, LISTS={app.config['PREDEFINED_LISTS_DIR']}")



# --- Загрузка анализаторов при старте ---
def initialize_analyzers():
    """Загружает Pymorphy3 и NLTK лемматизаторы."""
    try:
        app.logger.info("Loading morphological analyzers...")
        start_time = time.time()
        morph = load_pymorphy() # Загружает pymorphy3
        nltk_lemm = load_nltk_lemmatizer() # Загружает NLTK WordNet
        end_time = time.time()

        # Проверяем, загрузился ли хотя бы один анализатор
        if morph or nltk_lemm:
            app.logger.info(f"Morphological analyzers ready (initialized in {end_time - start_time:.2f} sec).")
            if morph: app.logger.info(" -> Pymorphy3 loaded.")
            else: app.logger.warning(" -> Pymorphy3 FAILED to load.")
            if nltk_lemm: app.logger.info(" -> NLTK WordNet Lemmatizer loaded.")
            else: app.logger.warning(" -> NLTK WordNet Lemmatizer FAILED to load.")
            return True
        else:
            app.logger.error("FAILED to load BOTH Pymorphy3 and NLTK Lemmatizer.")
            return False
    except SystemExit as e:
        # Перехватываем SystemExit, который может быть вызван при ошибке скачивания данных NLTK
        app.logger.critical(f"CRITICAL analyzer initialization error (SystemExit): {e}. Check NLTK data.", exc_info=True)
        return False
    except Exception as e:
        app.logger.critical(f"Unexpected critical error during analyzer initialization: {e}.", exc_info=True)
        return False

# Выполняем инициализацию и сохраняем статус
ANALYZERS_READY = initialize_analyzers()
app.config['ANALYZERS_READY'] = ANALYZERS_READY
if not ANALYZERS_READY:
    app.logger.error("="*50)
    app.logger.error("WARNING: MORPHOLOGICAL ANALYZERS FAILED TO LOAD!")
    app.logger.error("         Functionality requiring lemmatization/morphology will be unavailable or limited.")
    app.logger.error("="*50)
# --- КОНЕЦ ---


# --- Регистрация Blueprints ---
# Blueprint для инструмента подсветки
try:
    from tool_highlight.routes import highlight_bp
    app.register_blueprint(highlight_bp, url_prefix='/highlight')
    app.logger.info("Blueprint 'highlight_bp' registered successfully with prefix /highlight")
except ImportError:
    app.logger.error("Failed to import blueprint 'highlight_bp'. Highlight tool will be unavailable.")
except Exception as e:
     app.logger.error(f"Error registering blueprint 'highlight_bp': {e}", exc_info=True)


# Blueprint для инструмента сносок
try:
    from tool_footnotes.routes import footnotes_bp
    app.register_blueprint(footnotes_bp, url_prefix='/footnotes')
    app.logger.info("Blueprint 'footnotes_bp' registered successfully with prefix /footnotes")
except ImportError:
    app.logger.error("Failed to import blueprint 'footnotes_bp'. Footnotes tool will be unavailable.")
except Exception as e:
     app.logger.error(f"Error registering blueprint 'footnotes_bp': {e}", exc_info=True)
# --- КОНЕЦ РЕГИСТРАЦИИ ---


# --- Маршрут по умолчанию ---
@app.route('/')
def home():
    """Перенаправляет на главную страницу инструмента подсветки."""
    app.logger.info("Request to '/', redirecting to /highlight/...")
    return redirect(url_for('highlight.index')) # Перенаправляем на highlight.index
# --- КОНЕЦ ---


# --- Запуск приложения ---
# Этот блок выполняется только при запуске скрипта напрямую (python app.py),
# а не через WSGI сервер типа Gunicorn.
if __name__ == '__main__':
    if ANALYZERS_READY:
        app.logger.info("Starting Flask development server (Analyzers ready)...")
    else:
        app.logger.warning("Starting Flask development server (ANALYZERS FAILED TO LOAD!)...")

    # Для разработки используем встроенный сервер Flask с debug=True.
    # Для продакшена используйте Gunicorn или другой WSGI сервер и debug=False.
    # Пример запуска для разработки: flask run --host=0.0.0.0 --port=5000
    # Или напрямую:
    app.run(debug=True, host='0.0.0.0', port=5000)
# --- КОНЕЦ ---

# --- END OF FILE app.py ---