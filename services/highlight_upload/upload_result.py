"""
TypedDict for upload processing result.
"""

from typing import TypedDict, List, Optional


class UploadResult(TypedDict):
    """Result of file upload processing."""
    source_path: Optional[str]
    source_filename_original: Optional[str]
    words_path: Optional[str]
    words_filename_original: Optional[str]
    search_terms: List[str]
    is_docx_source: Optional[bool]
    file_ext: Optional[str]
    used_predefined_list_names: List[str]

