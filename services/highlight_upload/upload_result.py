"""
TypedDict for upload processing result.
"""

from typing import TypedDict, List, Optional


class UploadResult(TypedDict):
    """Result of file upload processing."""
    source_path: str
    source_filename_original: str
    words_path: Optional[str]
    words_filename_original: Optional[str]
    search_terms: List[str]
    is_docx_source: bool
    file_ext: str
    used_predefined_list_names: List[str]

