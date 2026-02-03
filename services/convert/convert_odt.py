"""
ODT -> DOCX conversion (odfpy).
"""

import os
from typing import List

import docx

from services.convert.base import ConvertToDocx

try:
    from odf import text, teletype
    from odf.opendocument import load
    _ODT_AVAILABLE = True
except ImportError:
    _ODT_AVAILABLE = False


class ConvertODT(ConvertToDocx):
    """Convert ODT to DOCX via odfpy."""

    def convert(self, abs_source_path: str, abs_result_path: str) -> None:
        if not _ODT_AVAILABLE:
            self._convert_error("odfpy not installed")
        if not os.path.exists(abs_source_path):
            self._convert_error(f"ODT file not found: {abs_source_path}")

        try:
            odt_doc = load(abs_source_path)
            docx_doc = docx.Document()
            text_content: List[str] = []
            for paragraph in odt_doc.getElementsByType(text.P):
                para_text: str = teletype.extractText(paragraph)
                if para_text.strip():
                    text_content.append(para_text)
            for para_text in text_content:
                docx_doc.add_paragraph(para_text)
            docx_doc.save(abs_result_path)
        except Exception as e:
            self._convert_error(str(e))
