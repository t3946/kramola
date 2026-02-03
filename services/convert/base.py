"""
Abstract base for converters to DOCX.
"""

from abc import ABC, abstractmethod


class ConvertError(Exception):
    """Raised when conversion cannot be performed."""


class ConvertToDocx(ABC):
    """Abstract converter: source format -> DOCX."""

    def _convert_error(self, message: str) -> None:
        raise ConvertError(message)

    @abstractmethod
    def convert(self, abs_source_path: str, abs_result_path: str) -> None:
        """
        Convert source file to DOCX.
        Raises ConvertError when conversion cannot be performed.

        Args:
            abs_source_path: Absolute path to source file.
            abs_result_path: Absolute path for output DOCX file.
        """
        pass
