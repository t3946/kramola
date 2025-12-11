"""
Service for handling file uploads and data preparation for highlight tool.
"""

import os
from typing import List, Dict
from flask import Request

from services.document_service import save_uploaded_file, extract_lines_from_docx
from services.highlight_upload.upload_result import UploadResult
from services.highlight_upload.upload_error import UploadError

try:
    import fitz  # PyMuPDF
    FIT_AVAILABLE = True
except ImportError:
    FIT_AVAILABLE = False

try:
    from utils import load_lines_from_txt
except ImportError:
    def load_lines_from_txt(filepath):
        raise FileNotFoundError(f"Utils module or function not found, cannot load {filepath}")


class HighlightUploadService:
    """Service for processing file uploads and preparing search terms."""

    @staticmethod
    def process_file_upload(
        request: Request,
        task_id: str,
        upload_dir: str,
        predefined_lists_dir: str,
        predefined_lists: dict
    ) -> UploadResult:
        """Process file uploads and prepare all search terms for highlight tool."""
        # 1. Process source file
        source_result = HighlightUploadService._process_source_file(
            request, task_id, upload_dir
        )
        
        # 2. Process words file (if provided)
        words_result = HighlightUploadService._process_words_file(
            request, task_id, upload_dir
        )
        
        # 3. Get search terms from all sources
        search_terms_result = HighlightUploadService._get_search_terms(
            request, task_id, words_result, predefined_lists_dir, predefined_lists
        )
        
        return {
            'source_path': source_result['path'],
            'source_filename_original': source_result['filename_original'],
            'words_path': words_result['path'],
            'words_filename_original': words_result['filename_original'],
            'search_terms': search_terms_result['search_terms'],
            'is_docx_source': source_result['is_docx'],
            'file_ext': source_result['file_ext'],
            'used_predefined_list_names': search_terms_result['used_list_names']
        }

    @staticmethod
    def _process_source_file(
        request: Request,
        task_id: str,
        upload_dir: str
    ) -> Dict:
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

        return {
            'path': source_path,
            'filename_original': source_filename_original,
            'is_docx': is_docx_source,
            'file_ext': file_ext
        }

    @staticmethod
    def _process_words_file(
        request: Request,
        task_id: str,
        upload_dir: str
    ) -> Dict:
        """Process and validate words file upload."""
        search_lines_from_file = []
        words_path = None
        words_filename_original = None
        
        words_file_input = request.files.get('words_file')
        
        if words_file_input and words_file_input.filename:
            words_filename_original = words_file_input.filename
            words_filename_lower = words_filename_original.lower()

            if not (words_filename_lower.endswith('.docx') or words_filename_lower.endswith('.xlsx')):
                raise UploadError('Файл слов должен быть в формате .docx или .xlsx', 400)
            
            if words_filename_lower.endswith('.docx'):
                words_filename_unique = f"words_{task_id}.docx"
                words_path = save_uploaded_file(words_file_input, upload_dir, words_filename_unique)
                if not words_path:
                    raise UploadError('Ошибка сохранения файла слов (.docx).', 500)
                try:
                    search_lines_from_file = extract_lines_from_docx(words_path)
                    if not isinstance(search_lines_from_file, list):
                        search_lines_from_file = []
                except Exception:
                    search_lines_from_file = []
            elif words_filename_lower.endswith('.xlsx'):
                # words_path is not set for xlsx currently
                search_lines_from_file = []
        
        return {
            'path': words_path,
            'filename_original': words_filename_original,
            'search_lines': search_lines_from_file
        }

    @staticmethod
    def _get_search_terms(
        request: Request,
        task_id: str,
        words_result: Dict,
        predefined_lists_dir: str,
        predefined_lists: dict
    ) -> Dict:
        """Get and combine search terms from all sources."""
        # 1. Words from file
        search_lines_from_file = words_result['search_lines']
        
        # 2. Words from text input
        search_lines_from_text = HighlightUploadService._process_text_input(request)
        
        # 3. Predefined lists from files
        predefined_result = HighlightUploadService._load_predefined_lists(
            request, predefined_lists_dir, predefined_lists
        )
        
        # 4. Foreign agents lists from Redis
        foreign_agents_result = HighlightUploadService._load_foreign_agents_lists(request)
        
        # 5. Combine all search lines
        all_search_lines = (
            search_lines_from_file +
            search_lines_from_text +
            predefined_result['search_lines'] +
            foreign_agents_result['search_lines']
        )
        
        used_predefined_list_names = (
            predefined_result['list_names'] +
            foreign_agents_result['list_names']
        )

        if not all_search_lines:
            raise UploadError('Укажите источник слов: файл, текстовое поле или выберите список.', 400)
        
        # Clean and deduplicate
        unique_lines_dict = {line.strip().lower(): line.strip() for line in all_search_lines if line.strip()}
        search_terms = list(unique_lines_dict.values())
        
        if not search_terms:
            raise UploadError('Предоставленные слова/фразы пусты или некорректны.', 400)
        
        return {
            'search_terms': search_terms,
            'used_list_names': used_predefined_list_names
        }

    @staticmethod
    def _process_text_input(request: Request) -> List[str]:
        """Process text input from textarea."""
        search_lines_from_text = []
        words_text_raw = request.form.get('words_text', '')
        
        if words_text_raw.strip():
            lines_from_text = words_text_raw.replace(',', '\n').splitlines()
            search_lines_from_text = [line.strip() for line in lines_from_text if line.strip()]

        return search_lines_from_text

    @staticmethod
    def _load_predefined_lists(
        request: Request,
        predefined_lists_dir: str,
        predefined_lists: dict
    ) -> Dict:
        """Load predefined lists from files."""
        additional_search_lines = []
        used_predefined_list_names = []
        selected_list_keys = request.form.getlist('predefined_list_keys')
        
        if selected_list_keys:
            for key in selected_list_keys:
                if not key or key not in predefined_lists:
                    continue
                filepath = os.path.join(predefined_lists_dir, f"{key}.txt")
                display_name = predefined_lists[key]
                try:
                    lines = load_lines_from_txt(filepath)
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    if cleaned_lines:
                        additional_search_lines.extend(cleaned_lines)
                        used_predefined_list_names.append(display_name)
                except (FileNotFoundError, Exception):
                    pass
        
        return {
            'search_lines': additional_search_lines,
            'list_names': used_predefined_list_names
        }

    @staticmethod
    def _load_foreign_agents_lists(request: Request) -> Dict:
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
            except Exception:
                pass
        
        if "Инагенты (Организации)" in predefined_lists_selected:
            try:
                from services.words_list.list_companies import ListCompanies
                lc = ListCompanies()
                companies_words = lc.load()
                foreign_agents_lines.extend(companies_words)
                used_list_names.append("Инагенты (Организации)")
            except Exception:
                pass
        
        return {
            'search_lines': foreign_agents_lines,
            'list_names': used_list_names
        }

