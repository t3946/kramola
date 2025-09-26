# --- START OF FILE pymorphy_service.py --- (FINALIZED)
from typing import List

import pymorphy3
import nltk
# NLTK импорты лемматизатора и стеммера будут внутри функций загрузки
import re
from collections import defaultdict # Оставляем, используется в get_highlight_phrase_map
import functools

# --- Константы и Глобальные переменные ---
MORPH = None
LEMMATIZER_EN = None
NLTK_DATA_PATH_CHECK = 'corpora/wordnet.zip'
STEMMER_RU = None
STEMMER_EN = None

CYRILLIC_PATTERN = re.compile('[а-яА-ЯёЁ]')
WORD_CLEAN_PATTERN = re.compile(r'[a-zA-Zа-яА-ЯёЁ]+(?:-[a-zA-Zа-яА-ЯёЁ]+)*', re.UNICODE)
WORD_TOKENIZE_PATTERN = re.compile(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', re.UNICODE)

# --- Инициализация NLTK, Pymorphy ---
def _ensure_nltk_data():
    try: nltk.data.find(NLTK_DATA_PATH_CHECK)
    except LookupError:
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
            nltk.data.find(NLTK_DATA_PATH_CHECK)
        except Exception: pass

def load_nltk_lemmatizer():
    global LEMMATIZER_EN
    if LEMMATIZER_EN is None:
        try:
            _ensure_nltk_data()
            from nltk.stem import WordNetLemmatizer
            LEMMATIZER_EN = WordNetLemmatizer()
            _ = LEMMATIZER_EN.lemmatize("testing", pos='v'); _ = LEMMATIZER_EN.lemmatize("tests", pos='n')
        except Exception: LEMMATIZER_EN = None
    return LEMMATIZER_EN

def load_pymorphy():
    global MORPH
    if MORPH is None:
        try: MORPH = pymorphy3.MorphAnalyzer(); MORPH.parse("тест")
        except Exception: MORPH = None
    return MORPH

def load_nltk_stemmers():
    global STEMMER_RU, STEMMER_EN
    if STEMMER_RU is None:
         try: from nltk.stem.snowball import SnowballStemmer; STEMMER_RU = SnowballStemmer('russian')
         except Exception: STEMMER_RU = 'failed'
    if STEMMER_EN is None:
         try: from nltk.stem.snowball import SnowballStemmer; STEMMER_EN = SnowballStemmer('english')
         except Exception: STEMMER_EN = 'failed'

def get_morph_analyzer():
    global MORPH
    if MORPH is None: load_pymorphy()
    return MORPH

def ensure_models_loaded():
    """Загружает Pymorphy, NLTK лемматизатор и стеммеры, если они еще не загружены."""
    load_pymorphy()
    load_nltk_lemmatizer()
    load_nltk_stemmers()

# --- Внутренние кэшируемые функции для логики ---
@functools.lru_cache(maxsize=100000)
def _get_lemma_cached(cleaned_word):
    if not cleaned_word: return cleaned_word
    global MORPH, LEMMATIZER_EN
    lemma = None; is_russian = bool(CYRILLIC_PATTERN.search(cleaned_word))
    if is_russian:
        if MORPH:
            try: lemma = MORPH.parse(cleaned_word)[0].normal_form
            except Exception: pass # lemma останется None
        lemma = lemma if lemma is not None else cleaned_word # Fallback
    else:
        if LEMMATIZER_EN:
            try:
                lemma_v = LEMMATIZER_EN.lemmatize(cleaned_word, pos='v')
                if lemma_v != cleaned_word: lemma = lemma_v
                else:
                    lemma_a = LEMMATIZER_EN.lemmatize(cleaned_word, pos='a')
                    if lemma_a != cleaned_word: lemma = lemma_a
                    else: lemma = LEMMATIZER_EN.lemmatize(cleaned_word, pos='n')
            except Exception: pass # lemma останется None
        lemma = lemma if lemma is not None else cleaned_word # Fallback
    return lemma

@functools.lru_cache(maxsize=100000)
def _get_stem_cached(cleaned_word):
    if not cleaned_word: return cleaned_word
    global STEMMER_RU, STEMMER_EN
    stem = None; is_russian = bool(CYRILLIC_PATTERN.search(cleaned_word))
    try:
        if is_russian:
            if STEMMER_RU and STEMMER_RU != 'failed': stem = STEMMER_RU.stem(cleaned_word)
        else:
            if STEMMER_EN and STEMMER_EN != 'failed': stem = STEMMER_EN.stem(cleaned_word)
    except Exception: pass
    return stem if stem is not None else cleaned_word

# --- Обертки для очистки слова и вызова кэшированных функций ---
def _clean_word(word):
     if not word or not isinstance(word, str): return None
     word_lower = word.lower().strip()
     match = WORD_CLEAN_PATTERN.search(word_lower)
     return match.group(0) if match else None

def _get_lemma(word):
    cleaned = _clean_word(word)
    return _get_lemma_cached(cleaned) if cleaned is not None else None

def _get_stem(word):
    cleaned = _clean_word(word)
    return _get_stem_cached(cleaned) if cleaned is not None else None

# --- НОВАЯ Унифицированная функция подготовки поисковых терминов ---
def prepare_search_terms(search_terms_list: List[str]):
    """
    Готовит данные для поиска слов и фраз.
    Возвращает словарь: {оригинальный_термин: {'type': 'word'/'phrase', 'data':...}}
    """
    ensure_models_loaded()
    prepared_data = {}; processed_terms_lower = set()
    if not isinstance(search_terms_list, (list, tuple, set)): return {}

    for term in search_terms_list:
        if not term or not isinstance(term, str): continue
        original_term = term.strip(); term_key_lower = original_term.lower()
        if not original_term or term_key_lower in processed_terms_lower: continue
        processed_terms_lower.add(term_key_lower)
        words_in_term = WORD_TOKENIZE_PATTERN.findall(original_term)
        is_phrase = len(words_in_term) > 1

        if is_phrase:
            lemmas = []; stems = []; valid_phrase = True
            for word in words_in_term:
                lemma = _get_lemma(word); stem = _get_stem(word)
                if lemma is None or stem is None: valid_phrase = False; break
                lemmas.append(lemma); stems.append(stem)
            if valid_phrase:
                prepared_data[original_term] = {
                    'type': 'phrase', 'original': original_term, 'words': words_in_term,
                    'lemmas': tuple(lemmas), 'stems': tuple(stems),
                    'lemmas_sorted': tuple(sorted(lemmas)), 'stems_sorted': tuple(sorted(stems)),
                }
        else:
            word_to_process = original_term
            lemma = _get_lemma(word_to_process); stem = _get_stem(word_to_process)
            prepared_data[original_term] = {
                'type': 'word', 'original': original_term, 'lower': term_key_lower,
                'lemma': lemma, 'stem': stem,
            }
    return prepared_data

# --- НОВЫЕ Функции-адаптеры, использующие подготовленные данные ---
def get_highlight_search_data(prepared_data):
    """Формирует данные для highlight_service из унифицированных данных."""
    search_lemmas_set = set(); search_stems_set = set()
    for data in prepared_data.values():
        if data['type'] == 'word':
            if data['lemma']: search_lemmas_set.add(data['lemma'])
            if data['stem']: search_stems_set.add(data['stem'])
    return {'lemmas': search_lemmas_set, 'stems': search_stems_set}

def get_highlight_phrase_map(prepared_data):
     """Формирует карту фраз (с учетом порядка) для highlight_service."""
     phrase_lemmas_map = defaultdict(list)
     for data in prepared_data.values():
         if data['type'] == 'phrase' and data.get('lemmas'):
             phrase_lemmas_map[data['lemmas']].append(data['original'])
     return dict(phrase_lemmas_map)

def get_footnotes_word_maps(prepared_data):
    """Формирует карты слов (lemma -> info, stem -> info) для footnotes_service."""
    lemmas_map = {}; stems_map = {}
    for term, data in prepared_data.items():
         if data['type'] == 'word':
              if data['lemma'] and data['stem']:
                  info = {'original': data['original'], 'lemma': data['lemma'], 'stem': data['stem']}
                  if data['lemma'] not in lemmas_map: lemmas_map[data['lemma']] = info
                  if data['stem'] not in stems_map: stems_map[data['stem']] = info
    return lemmas_map, stems_map

def get_footnotes_phrase_maps(prepared_data):
    """Формирует карты фраз (БЕЗ учета порядка) для footnotes_service."""
    phrase_lemmas_map = {}; phrase_stems_map = {}
    for term, data in prepared_data.items():
        if data['type'] == 'phrase':
            lemmas_key = data.get('lemmas_sorted'); stems_key = data.get('stems_sorted')
            if lemmas_key and stems_key:
                info = {'original': data['original'], 'lemma_key': lemmas_key, 'stem_key': stems_key}
                if lemmas_key not in phrase_lemmas_map: phrase_lemmas_map[lemmas_key] = info
                if stems_key not in phrase_stems_map: phrase_stems_map[stems_key] = info
    return phrase_lemmas_map, phrase_stems_map

# --- УДАЛЕННЫЕ старые функции подготовки ---
# def get_search_maps_data(search_words): ...
# def get_search_phrase_maps_data(phrases_lines): ...

# --- Функция сброса кэша ---
def reset_caches():
    """Сбрасывает (очищает) LRU кэши лемм и стеммов."""
    try: _get_lemma_cached.cache_clear()
    except AttributeError: pass
    try: _get_stem_cached.cache_clear()
    except AttributeError: pass

# --- END OF FILE pymorphy_service.py --- (FINALIZED)