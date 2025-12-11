"""
Service for handling file uploads and data preparation for highlight tool.
"""

import os
from typing import TypedDict, List, Optional, Tuple
from flask import Request

from services.document_service import save_uploaded_file, extract_lines_from_docx

try:
    import fitz  # PyMuPDF
    FIT_AVAILABLE = True
except ImportError:
    FIT_AVAILABLE = False

try:
    from utils import load_lines_from_txt
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    def load_lines_from_txt(filepath):
        raise FileNotFoundError(f"Utils module or function not found, cannot load {filepath}")


class UploadResult(TypedDict):
    """Result of file upload processing."""
    source_path: str
    source_filename_original: str
    words_path: Optional[str]
    words_filename_original: Optional[str]
    all_search_lines_clean: List[str]
    is_docx_source: bool
    file_ext: str
    used_predefined_list_names: List[str]


class UploadError(Exception):
    """Custom exception for upload errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def process_file_upload(
    request: Request,
    task_id: str,
    upload_dir: str,
    predefined_lists_dir: str,
    predefined_lists: dict,
    logger
) -> UploadResult:
    """
    Process file uploads and prepare all search terms for highlight tool.
    
    Args:
        request: Flask request object
        task_id: Unique task identifier
        upload_dir: Directory for saving uploaded files
        predefined_lists_dir: Directory with predefined list files
        predefined_lists: Dictionary mapping list keys to display names
        logger: Logger instance
    
    Returns:
        UploadResult with all processed data
    
    Raises:
        UploadError: If validation fails or processing error occurs
    """
    # 1. Process source file
    source_result = _process_source_file(request, task_id, upload_dir, logger)
    
    # 2. Process words file (if provided)
    words_result = _process_words_file(request, task_id, upload_dir, logger)
    
    # 3. Process text input
    search_lines_from_text = _process_text_input(request, task_id, logger)
    
    # 4. Load predefined lists
    predefined_result = _load_predefined_lists(
        request, task_id, predefined_lists_dir, predefined_lists, logger
    )
    
    # 5. Load foreign agents lists from Redis
    foreign_agents_result = _load_foreign_agents_lists(request, task_id, logger)
    
    # 6. Combine and clean all search lines
    all_search_lines = (
        words_result['search_lines'] +
        search_lines_from_text +
        predefined_result['search_lines'] +
        foreign_agents_result['search_lines']
    )
    
    used_predefined_list_names = (
        predefined_result['list_names'] +
        foreign_agents_result['list_names']
    )

    if not all_search_lines:
        logger.error(f"[Req {task_id}] No word source provided (file, text, or predefined).")
        raise UploadError('Укажите источник слов: файл, текстовое поле или выберите список.', 400)
    
    # Clean and deduplicate
    unique_lines_dict = {line.strip().lower(): line.strip() for line in all_search_lines if line.strip()}
    all_search_lines_clean = list(unique_lines_dict.values())
    
    if not all_search_lines_clean:
        logger.error(f"[Req {task_id}] All search lines are empty after cleaning.")
        raise UploadError('Предоставленные слова/фразы пусты или некорректны.', 400)
    

    
    return {
        'source_path': source_result['path'],
        'source_filename_original': source_result['filename_original'],
        'words_path': words_result['path'],
        'words_filename_original': words_result['filename_original'],
        'all_search_lines_clean': all_search_lines_clean,
        'is_docx_source': source_result['is_docx'],
        'file_ext': source_result['file_ext'],
        'used_predefined_list_names': used_predefined_list_names
    }


def _process_source_file(
    request: Request,
    task_id: str,
    upload_dir: str,
    logger
) -> dict:
    """Process and validate source file upload."""
    if 'source_file' not in request.files or not request.files['source_file'].filename:
        raise UploadError('Загрузите исходный документ (.docx или .pdf)', 400)
    
    source_file = request.files['source_file']
    source_filename_original = source_file.filename
    source_filename_lower = source_filename_original.lower()
    is_docx_source = source_filename_lower.endswith('.docx')
    is_pdf_source = source_filename_lower.endswith('.pdf')
    
    if not is_docx_source and not is_pdf_source:
        raise UploadError('Недопустимый формат исходного файла. Загрузите .docx или .pdf', 400)
    
    if is_pdf_source and not FIT_AVAILABLE:
        raise UploadError('Обработка PDF файлов недоступна на сервере (PyMuPDF).', 400)
    
    file_ext = ".docx" if is_docx_source else ".pdf"
    source_filename_unique = f"source_{task_id}{file_ext}"
    source_path = save_uploaded_file(source_file, upload_dir, source_filename_unique)
    
    if not source_path:
        raise UploadError('Ошибка при сохранении исходного документа.', 500)
    
    logger.info(f"[Req {task_id}] Source file '{source_filename_original}' saved as '{source_filename_unique}'")

    return {
        'path': source_path,
        'filename_original': source_filename_original,
        'is_docx': is_docx_source,
        'file_ext': file_ext
    }


def _process_words_file(
    request: Request,
    task_id: str,
    upload_dir: str,
    logger
) -> dict:
    """Process and validate words file upload."""
    search_lines_from_file = []
    words_path = None
    words_filename_original = None
    
    words_file_input = request.files.get('words_file')
    
    if words_file_input and words_file_input.filename:
        words_filename_original = words_file_input.filename
        words_filename_lower = words_filename_original.lower()
        logger.info(f"[Req {task_id}] Received words_file: '{words_filename_original}'")

        if not (words_filename_lower.endswith('.docx') or words_filename_lower.endswith('.xlsx')):
            raise UploadError('Файл слов должен быть в формате .docx или .xlsx', 400)
        
        if words_filename_lower.endswith('.docx'):
            words_filename_unique = f"words_{task_id}.docx"
            words_path = save_uploaded_file(words_file_input, upload_dir, words_filename_unique)
            if not words_path:
                raise UploadError('Ошибка сохранения файла слов (.docx).', 500)
            logger.info(f"[Req {task_id}] Words file (.docx) saved as '{words_filename_unique}'")
            try:
                search_lines_from_file = extract_lines_from_docx(words_path)
                if not isinstance(search_lines_from_file, list):
                    search_lines_from_file = []
                logger.info(
                    f"[Req {task_id}] Extracted {len(search_lines_from_file)} lines from '{words_filename_original}'")
            except Exception as e:
                logger.error(f"[Req {task_id}] Error reading DOCX words file '{words_path}': {e}", exc_info=True)
                search_lines_from_file = []
        elif words_filename_lower.endswith('.xlsx'):
            logger.warning(
                f"[Req {task_id}] XLSX words file '{words_filename_original}' received. "
                f"Backend will treat as empty unless explicit XLSX parsing is added.")
            # words_path is not set for xlsx currently
            search_lines_from_file = []
    
    return {
        'path': words_path,
        'filename_original': words_filename_original,
        'search_lines': search_lines_from_file
    }


def _process_text_input(
    request: Request,
    task_id: str,
    logger
) -> List[str]:
    """Process text input from textarea."""
    search_lines_from_text = []
    words_text_raw = request.form.get('words_text', '')
    
    if words_text_raw.strip():
        lines_from_text = words_text_raw.replace(',', '\n').splitlines()
        search_lines_from_text = [line.strip() for line in lines_from_text if line.strip()]
        logger.info(f"[Req {task_id}] Received {len(search_lines_from_text)} lines from textarea.")

    return search_lines_from_text


def _load_predefined_lists(
    request: Request,
    task_id: str,
    predefined_lists_dir: str,
    predefined_lists: dict,
    logger
) -> dict:
    """Load predefined lists from files."""
    additional_search_lines = []
    used_predefined_list_names = []
    selected_list_keys = request.form.getlist('predefined_list_keys')
    
    if selected_list_keys:
        logger.info(f"[Req {task_id}] Selected predefined lists: {selected_list_keys}")
        for key in selected_list_keys:
            if not key or key not in predefined_lists:
                logger.warning(f"[Req {task_id}] Invalid or unknown predefined list key: '{key}'")
                continue
            filepath = os.path.join(predefined_lists_dir, f"{key}.txt")
            display_name = predefined_lists[key]
            try:
                lines = load_lines_from_txt(filepath)
                cleaned_lines = [line.strip() for line in lines if line.strip()]
                if cleaned_lines:
                    additional_search_lines.extend(cleaned_lines)
                    used_predefined_list_names.append(display_name)
                    logger.info(
                        f"[Req {task_id}] Loaded {len(cleaned_lines)} lines from predefined list "
                        f"'{display_name}' ({key}.txt)")
            except FileNotFoundError:
                logger.error(f"[Req {task_id}] Predefined list file not found: {filepath}")
            except Exception as e:
                logger.error(
                    f"[Req {task_id}] Error loading predefined list '{display_name}' ({key}.txt): {e}",
                    exc_info=True
                )
    
    return {
        'search_lines': additional_search_lines,
        'list_names': used_predefined_list_names
    }


def _load_foreign_agents_lists(
    request: Request,
    task_id: str,
    logger
) -> dict:
    """Load foreign agents lists from Redis if selected."""
    foreign_agents_lines = []
    used_list_names = []
    predefined_lists_selected = request.form.getlist('predefined_lists[]')
    
    if "Инагенты (ФИО)" in predefined_lists_selected:
        try:
            from services.words_list.list_persons import ListPersons
            lp = ListPersons()
            persons_words = lp.load()
            foreign_agents_lines.extend(persons_words)
            used_list_names.append("Инагенты (ФИО)")
            logger.info(
                f"[Req {task_id}] Selected 'Инагенты (ФИО)': loaded {len(persons_words)} names from ListPersons"
            )
        except Exception as e:
            logger.error(f"[Req {task_id}] Error loading 'Инагенты (ФИО)' list: {e}", exc_info=True)
    
    if "Инагенты (Организации)" in predefined_lists_selected:
        try:
            from services.words_list.list_companies import ListCompanies
            lc = ListCompanies()
            companies_words = lc.load()
            foreign_agents_lines.extend(companies_words)
            used_list_names.append("Инагенты (Организации)")
            logger.info(
                f"[Req {task_id}] Selected 'Инагенты (Организации)': loaded {len(companies_words)} names from ListCompanies"
            )
        except Exception as e:
            logger.error(f"[Req {task_id}] Error loading 'Инагенты (Организации)' list: {e}", exc_info=True)
    
    return {
        'search_lines': foreign_agents_lines,
        'list_names': used_list_names
    }

