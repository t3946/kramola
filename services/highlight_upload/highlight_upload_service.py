"""
Service for handling file uploads and data preparation for highlight tool.
"""

import os
import logging
from typing import List, Dict
from flask import Request

from services.document_service import save_uploaded_file, extract_lines_from_docx, convert_odt_to_docx
from services.utils.load_lines_from_txt import load_lines_from_txt
from services.highlight_upload.upload_result import UploadResult
from services.highlight_upload.upload_error import UploadError
from services.analysis.analysis_data import AnalysisData
from services.words_list import PredefinedListKey

logger = logging.getLogger(__name__)

try:
    import pymupdf

    FIT_AVAILABLE = True
except ImportError:
    FIT_AVAILABLE = False


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
            request, words_result, predefined_lists_dir, predefined_lists
        )

        return {
            'source_path': source_result['path'],
            'source_filename_original': source_result['filename_original'],
            'words_path': words_result['path'],
            'words_filename_original': words_result['filename_original'],
            'search_terms': search_terms_result['search_terms'],
            'is_docx_source': source_result['is_docx'],
            'file_ext': source_result['file_ext'],
            'used_predefined_list_names': search_terms_result['used_list_names'],
            'selected_list_keys': search_terms_result.get('selected_list_keys', [])
        }

    @staticmethod
    def _process_source_file(
            request: Request,
            task_id: str,
            upload_dir: str
    ) -> Dict:
        """Process and validate source file upload."""
        if 'source_file' not in request.files or not request.files['source_file'].filename:
            raise UploadError('Загрузите исходный документ (.docx, .pdf или .odt)', 400)

        source_file = request.files['source_file']
        source_filename_original = source_file.filename
        source_filename_lower = source_filename_original.lower()
        is_docx_source = source_filename_lower.endswith('.docx')
        is_pdf_source = source_filename_lower.endswith('.pdf')
        is_odt_source = source_filename_lower.endswith('.odt')

        if not is_docx_source and not is_pdf_source and not is_odt_source:
            raise UploadError('Недопустимый формат исходного файла. Загрузите .docx, .pdf или .odt', 400)

        if is_pdf_source and not FIT_AVAILABLE:
            raise UploadError('Обработка PDF файлов недоступна на сервере (PyMuPDF).', 400)

        # Если это ODT файл, сначала сохраняем его, затем конвертируем в DOCX
        if is_odt_source:
            # Сохраняем оригинальный ODT файл
            odt_filename_unique = f"source_{task_id}.odt"
            odt_path = save_uploaded_file(source_file, upload_dir, odt_filename_unique)
            
            if not odt_path:
                raise UploadError('Ошибка при сохранении исходного документа.', 500)
            
            # Конвертируем ODT в DOCX
            docx_filename_unique = f"source_{task_id}.docx"
            docx_path = os.path.join(upload_dir, docx_filename_unique)
            
            if not convert_odt_to_docx(odt_path, docx_path):
                # Удаляем ODT файл при ошибке конвертации
                try:
                    if os.path.exists(odt_path):
                        os.remove(odt_path)
                except Exception as e:
                    logger.error(e)
                    pass
                raise UploadError('Ошибка при конвертации ODT файла в DOCX. Убедитесь, что библиотека odfpy установлена.', 500)
            
            # Удаляем временный ODT файл после успешной конвертации
            try:
                if os.path.exists(odt_path):
                    os.remove(odt_path)
            except Exception as e:
                logger.warning(f"Не удалось удалить временный ODT файл {odt_path}: {e}")
            
            source_path = docx_path
            file_ext = ".docx"
            is_docx_source = True  # После конвертации обрабатываем как DOCX
        else:
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

            allowed_extensions: list[str] = [
                '.docx',
                '.xlsx',
                '.txt',
            ]

            is_allowed = any(words_filename_lower.endswith(ext) for ext in allowed_extensions)

            if not is_allowed:
                allowed_formats = ', '.join(allowed_extensions)
                raise UploadError(f'Файл слов должен быть в формате {allowed_formats}.', 400)

            if words_filename_lower.endswith('.docx'):
                words_filename_unique = f"words_{task_id}.docx"
                words_path = save_uploaded_file(words_file_input, upload_dir, words_filename_unique)
                if not words_path:
                    raise UploadError('Ошибка сохранения файла слов (.docx).', 500)
                search_lines_from_file = extract_lines_from_docx(words_path)
                if not isinstance(search_lines_from_file, list):
                    search_lines_from_file = []
            elif words_filename_lower.endswith('.xlsx'):
                # words_path is not set for xlsx currently
                search_lines_from_file = []
            elif words_filename_lower.endswith('.txt'):
                words_filename_unique = f"words_{task_id}.txt"
                words_path = save_uploaded_file(words_file_input, upload_dir, words_filename_unique)

                if not words_path:
                    raise UploadError('Ошибка сохранения файла слов (.txt).', 500)

                search_lines_from_file = load_lines_from_txt(words_path)

        return {
            'path': words_path,
            'filename_original': words_filename_original,
            'search_lines': search_lines_from_file
        }

    @staticmethod
    def _get_search_terms(
            request: Request,
            words_result: Dict,
            predefined_lists_dir: str,
            predefined_lists: dict
    ) -> Dict:
        """Get and combine search terms from all sources."""
        # 1. Words from file
        search_lines_from_file = words_result['search_lines']

        # 2. Words from text input
        search_lines_from_text = HighlightUploadService._process_text_input(request)

        # 3. Predefined lists (from files and Redis)
        predefined_result = HighlightUploadService._load_predefined_lists(
            request, predefined_lists_dir, predefined_lists
        )

        # 4. Combine initial search lines (before predefined lists processing)
        all_search_lines = (
                search_lines_from_file +
                search_lines_from_text
        )

        used_predefined_list_names = []

        if not len(predefined_result.get('selected_list_keys', [])) and not all_search_lines and not search_lines_from_text:
            raise UploadError('Укажите источник слов: файл, текстовое поле или выберите список.', 400)

        # Clean and deduplicate
        unique_lines_dict = {line.strip().lower(): line.strip() for line in all_search_lines if line.strip()}
        search_terms = list(unique_lines_dict.values())

        # 5. Load predefined lists using AnalysisData
        selected_list_keys = predefined_result.get('selected_list_keys', [])

        if selected_list_keys:
            analysis_data = AnalysisData()
            analysis_data.load_predefined_lists(selected_list_keys)

            # Extract texts from loaded phrases
            search_terms_from_lists = list(analysis_data.phrases.keys())

            # Collect used list names
            for key in selected_list_keys:
                if key and key in predefined_lists:
                    display_name = predefined_lists.get(key, key)
                    used_predefined_list_names.append(display_name)

            # Combine with existing search_terms and deduplicate again
            all_terms_with_lists = search_terms + search_terms_from_lists
            unique_terms_dict = {term.strip().lower(): term.strip() for term in all_terms_with_lists if term.strip()}
            search_terms = list(unique_terms_dict.values())

        return {
            'search_terms': search_terms,
            'used_list_names': used_predefined_list_names,
            'selected_list_keys': selected_list_keys
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
        """Get selected predefined list keys. Actual loading is done in universal code section."""
        selected_list_keys = request.form.getlist('predefined_list_keys')

        return {
            'search_lines': [],
            'list_names': [],
            'selected_list_keys': selected_list_keys,
        }

