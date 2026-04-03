"""
Service for handling file uploads and data preparation for highlight tool.
"""

import os
import logging
from typing import List, Dict, Union
from flask import Request, current_app

from services.document_service import save_uploaded_file, extract_lines_from_docx
from services.convert import ConvertODT, ConvertDOC, ConvertError
from services.fulltext_search import Phrase
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
        words_result = HighlightUploadService._process_user_file(
            request, task_id, upload_dir, file_key='words_file', path_prefix='words'
        )

        # 3. Process exclude file/text (same source logic as words)
        exclude_result = HighlightUploadService._process_user_file(
            request, task_id, upload_dir, file_key='exclude_file', path_prefix='exclude'
        )
        exclude_lines = exclude_result['search_lines'] + HighlightUploadService._process_text_input(
            request, form_key='exclude_text'
        )

        # 4. Get search terms from all sources
        search_terms_result = HighlightUploadService._get_search_terms(
            request, words_result, predefined_lists_dir, predefined_lists
        )

        return {
            'source_path': source_result['path'],
            'source_filename_original': source_result['filename_original'],
            'words_path': words_result['path'],
            'words_filename_original': words_result['filename_original'],
            'search_terms': search_terms_result['search_terms'],
            'user_search_terms': search_terms_result.get('user_search_terms', []),
            'exclude_path': exclude_result['path'],
            'exclude_lines': exclude_lines,
            'is_docx_source': source_result['is_docx'],
            'file_ext': source_result['file_ext'],
            'used_predefined_list_names': search_terms_result['used_list_names'],
            'selected_list_keys': search_terms_result.get('selected_list_keys', []),
            'inagents_fiz_search_text': search_terms_result.get(
                'inagents_fiz_search_text', True
            ),
            'inagents_fiz_search_surnames': search_terms_result.get(
                'inagents_fiz_search_surnames', True
            ),
            'inagents_fiz_search_full_names': search_terms_result.get(
                'inagents_fiz_search_full_names', True
            ),
        }

    @staticmethod
    def _process_source_file(
            request: Request,
            task_id: str,
            upload_dir: str
    ) -> Dict:
        # get ext
        source_file = request.files['source_file']
        filename = source_file.filename
        ext = os.path.splitext(filename)[1].lower()

        # [start] validate format
        allowed_ext = SourceFormat.extensions()
        formats_str = ", ".join(allowed_ext)

        if 'source_file' not in request.files or not request.files['source_file'].filename:
            raise UploadError(f"Загрузите исходный документ ({formats_str})", 400)

        if ext not in allowed_ext:
            raise UploadError(f"Недопустимый формат исходного файла. Загрузите {formats_str}", 400)
        # [end]

        source_path = save_uploaded_file(source_file, upload_dir, f"source_{task_id}{ext}")

        # [start] convert to docx
        to_docx = {SourceFormat.DOC.value: ConvertDOC(), SourceFormat.ODT.value: ConvertODT()}
        if ext in to_docx:
            source_path = HighlightUploadService._convert_upload_to_docx(
                source_path, upload_dir, task_id, to_docx[ext]
            )
            ext = SourceFormat.DOCX.value
        # [end]

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
    def _process_user_file(
            request: Request,
            task_id: str,
            upload_dir: str,
            file_key: str = 'words_file',
            path_prefix: str = 'words'
    ) -> Dict:
        """Process and validate user list file (words or exclude). Same reading logic for both."""
        search_lines_from_file: List[str] = []
        file_path = None
        filename_original = None

        file_input = request.files.get(file_key)

        if file_input and file_input.filename:
            filename_original = file_input.filename
            ext: str = os.path.splitext(filename_original)[1].lower()
            allowed = WordsFormat.extensions()

            if ext not in allowed:
                raise UploadError(
                    f'Файл должен быть в формате {", ".join(allowed)}.', 400
                )

            if ext == WordsFormat.DOCX.value:
                filename_unique = f"{path_prefix}_{task_id}{WordsFormat.DOCX}"
                file_path = save_uploaded_file(file_input, upload_dir, filename_unique)

                if not file_path:
                    raise UploadError(f'Ошибка сохранения файла (.docx).', 500)

                search_lines_from_file = extract_lines_from_docx(file_path)
                if not isinstance(search_lines_from_file, list):
                    search_lines_from_file = []

            elif ext == WordsFormat.XLSX.value:
                search_lines_from_file = []
            elif ext == WordsFormat.TXT.value:
                filename_unique = f"{path_prefix}_{task_id}{WordsFormat.TXT}"
                file_path = save_uploaded_file(file_input, upload_dir, filename_unique)

                if not file_path:
                    raise UploadError(f'Ошибка сохранения файла (.txt).', 500)

                search_lines_from_file = load_lines_from_txt(file_path)

        return {
            'path': file_path,
            'filename_original': filename_original,
            'search_lines': [line.strip() for line in search_lines_from_file if line and line.strip()]
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
        search_lines_from_text = HighlightUploadService._process_text_input(request, form_key='words_text')

        # 3. Predefined lists (from files and Redis)
        predefined_result = HighlightUploadService._load_predefined_lists(
            request, predefined_lists_dir, predefined_lists
        )

        # 4. Combine initial search lines (before predefined lists processing)
        user_search_terms: list[str] = (
                search_lines_from_file +
                search_lines_from_text
        )
        selected_list_keys = predefined_result.get('selected_list_keys', [])
        used_predefined_list_names = []

        if not len(selected_list_keys) and not user_search_terms and not search_lines_from_text:
            raise UploadError('Укажите источник слов: файл, текстовое поле или выберите список.', 400)

        search_terms = []

        # 5. Load predefined lists using AnalysisData
        if selected_list_keys:
            analysis_data = AnalysisData()
            analysis_data.load_predefined_lists(
                selected_list_keys,
                inagents_fiz_search_text=predefined_result.get(
                    'inagents_fiz_search_text', True
                ),
                inagents_fiz_search_surnames=predefined_result.get(
                    'inagents_fiz_search_surnames', True
                ),
                inagents_fiz_search_full_names=predefined_result.get(
                    'inagents_fiz_search_full_names', True
                ),
            )

            # Extract texts from loaded phrases
            search_terms_from_lists: list[Phrase] = analysis_data.phrases

            # Collect used list names
            for key in selected_list_keys:
                if key and key in predefined_lists:
                    display_name = predefined_lists.get(key, key)
                    used_predefined_list_names.append(display_name)

            # Combine with existing search_terms and deduplicate again
            all_terms_with_lists: list[Phrase] = search_terms + search_terms_from_lists
            unique_terms_dict = {phrase.phrase.lower(): phrase.phrase for phrase in all_terms_with_lists}
            search_terms = list(unique_terms_dict.values())

        return {
            'search_terms': search_terms,
            'user_search_terms': user_search_terms,
            'used_list_names': used_predefined_list_names,
            'selected_list_keys': selected_list_keys,
            'inagents_fiz_search_text': predefined_result.get(
                'inagents_fiz_search_text', True
            ),
            'inagents_fiz_search_surnames': predefined_result.get(
                'inagents_fiz_search_surnames', True
            ),
            'inagents_fiz_search_full_names': predefined_result.get(
                'inagents_fiz_search_full_names', True
            ),
        }

    @staticmethod
    def _process_text_input(request: Request, form_key: str = 'words_text') -> List[str]:
        """Process text input from textarea (words or exclude)."""
        search_lines_from_text: List[str] = []
        raw = request.form.get(form_key, '')

        if raw.strip():
            lines_from_text = raw.replace(',', '\n').splitlines()
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
        inagents_text: bool
        inagents_surnames: bool
        inagents_full_names: bool

        if request.form.get('inagents_fiz_options_version') == '1':
            by_surname = request.form.get('inagents_fiz_by_surname') == '1'
            inagents_text = by_surname
            inagents_surnames = by_surname
            inagents_full_names = request.form.get('inagents_fiz_search_full_names') == '1'
        else:
            inagents_text = True
            inagents_surnames = True
            inagents_full_names = True

        return {
            'search_lines': [],
            'list_names': [],
            'selected_list_keys': selected_list_keys,
            'inagents_fiz_search_text': inagents_text,
            'inagents_fiz_search_surnames': inagents_surnames,
            'inagents_fiz_search_full_names': inagents_full_names,
        }
