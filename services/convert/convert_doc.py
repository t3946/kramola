"""
DOC -> DOCX conversion (LibreOffice headless).
"""

import os
import subprocess

from services.convert.base import ConvertToDocx


class ConvertDOC(ConvertToDocx):
    """Convert DOC to DOCX via LibreOffice --headless."""

    def convert(self, abs_source_path: str, abs_result_path: str) -> None:
        if not os.path.exists(abs_source_path):
            self._convert_error(f"DOC file not found: {abs_source_path}")

        outdir = os.path.dirname(abs_result_path)
        os.makedirs(outdir, exist_ok=True)

        try:
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'docx',
                abs_source_path,
                '--outdir', outdir
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            libreoffice_output = os.path.join(
                outdir,
                os.path.splitext(os.path.basename(abs_source_path))[0] + '.docx'
            )
            if os.path.abspath(libreoffice_output) != os.path.abspath(abs_result_path):
                os.replace(libreoffice_output, abs_result_path)
        except subprocess.CalledProcessError as e:
            self._convert_error(str(e))
        except Exception as e:
            self._convert_error(str(e))
