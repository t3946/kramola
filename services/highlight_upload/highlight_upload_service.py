"""
Service for handling file uploads and data preparation for highlight tool.
"""

import os
import logging
from typing import List, Dict, Union
from flask import Request

from services.document_service import save_uploaded_file, extract_lines_from_docx
from services.convert import ConvertODT, ConvertDOC, ConvertError
from services.utils.load_lines_from_txt import load_lines_from_txt
from services.highlight_upload.upload_result import UploadResult
from services.highlight_upload.upload_error import UploadError
from services.highlight_upload.enum import SourceFormat, WordsFormat
from services.analysis.analysis_data import AnalysisData

logger = logging.getLogger(__name__)


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
        #get ext
        source_file = request.files['source_file']
        filename = source_file.filename
        ext = os.path.splitext(filename)[1].lower()

        #[start] validate format
        allowed_ext = SourceFormat.extensions()
        formats_str = ", ".join(allowed_ext)

        if 'source_file' not in request.files or not request.files['source_file'].filename:
            raise UploadError(f"Загрузите исходный документ ({formats_str})", 400)

        if ext not in allowed_ext:
            raise UploadError(f"Недопустимый формат исходного файла. Загрузите {formats_str}", 400)
        #[end]

        source_path = save_uploaded_file(source_file, upload_dir, f"source_{task_id}{ext}")

        #[start] convert to docx
        to_docx = {SourceFormat.DOC.value: ConvertDOC(), SourceFormat.ODT.value: ConvertODT()}
        if ext in to_docx:
            source_path = HighlightUploadService._convert_upload_to_docx(
                source_path, upload_dir, task_id, to_docx[ext]
            )
            ext = SourceFormat.DOCX.value
        #[end]

        return {
            'path': source_path,
            'filename_original': filename,
            'is_docx': ext == SourceFormat.DOCX.value,
            'file_ext': ext
        }

    @staticmethod
    def _convert_upload_to_docx(
            temp_path: str,
            upload_dir: str,
            task_id: str,
            converter: Union[ConvertDOC, ConvertODT],
    ) -> str:
        docx_path = os.path.join(upload_dir, f"source_{task_id}.docx")

        try:
            converter.convert(temp_path, docx_path)
        except ConvertError:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            source_ext = os.path.splitext(temp_path)[1].lstrip('.')
            raise UploadError(f'Ошибка конвертации {source_ext} в docx', 500)

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return docx_path

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
            words_ext = os.path.splitext(words_filename_original)[1].lower()
            allowed_words = WordsFormat.extensions()
            if words_ext not in allowed_words:
                raise UploadError(
                    f'Файл слов должен быть в формате {", ".join(allowed_words)}.', 400
                )
            if words_ext == WordsFormat.DOCX:
                words_filename_unique = f"words_{task_id}{WordsFormat.DOCX}"
                words_path = save_uploaded_file(words_file_input, upload_dir, words_filename_unique)
                if not words_path:
                    raise UploadError('Ошибка сохранения файла слов (.docx).', 500)
                search_lines_from_file = extract_lines_from_docx(words_path)
                if not isinstance(search_lines_from_file, list):
                    search_lines_from_file = []
            elif words_ext == WordsFormat.XLSX:
                search_lines_from_file = []
            elif words_ext == WordsFormat.TXT:
                words_filename_unique = f"words_{task_id}{WordsFormat.TXT}"
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

