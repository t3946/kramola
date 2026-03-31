#!/usr/bin/env python3
"""
Converts PDF file to DOCX format.
usage: python commands/convert_pdf_to_docx.py input.pdf output.docx
"""

import argparse
import importlib.util
import logging
import sys
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "convert_pdf_to_docx.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def is_pdf2docx_available() -> bool:
    """Check whether pdf2docx package is installed."""
    return importlib.util.find_spec("pdf2docx") is not None


def convert_pdf_to_docx(pdf_path: Path, docx_path: Path) -> bool:
    """Convert PDF file to DOCX."""
    from pdf2docx import Converter

    logger.info("Converting PDF to DOCX: %s -> %s", pdf_path, docx_path)

    converter: Converter = Converter(str(pdf_path))
    converter.convert(str(docx_path))
    converter.close()

    logger.info("Successfully converted to: %s", docx_path)
    return True


def main() -> int:
    """Main function for converting PDF to DOCX."""
    parser = argparse.ArgumentParser(description="Convert PDF file to DOCX")
    parser.add_argument("input", type=str, help="Path to input PDF file")
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        help="Path to output DOCX file (optional)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting PDF to DOCX conversion")
    logger.info("=" * 60)

    pdf_path: Path = Path(args.input).resolve()

    if not pdf_path.exists():
        logger.error("Input file not found: %s", pdf_path)
        return 1

    if pdf_path.suffix.lower() != ".pdf":
        logger.warning("File extension is not .pdf: %s", pdf_path.suffix)

    if not is_pdf2docx_available():
        logger.error("pdf2docx is not installed in current environment")
        logger.error("Install with: pip install pdf2docx")
        logger.error("Or install all requirements: pip install -r requirements.txt")
        return 1

    if args.output:
        docx_path: Path = Path(args.output).resolve()
    else:
        docx_path = pdf_path.with_suffix(".docx")

    docx_path.parent.mkdir(parents=True, exist_ok=True)

    if convert_pdf_to_docx(pdf_path=pdf_path, docx_path=docx_path):
        logger.info("=" * 60)
        logger.info("Conversion completed successfully")
        logger.info("=" * 60)
        return 0

    logger.error("=" * 60)
    logger.error("Conversion failed")
    logger.error("=" * 60)
    return 1


if __name__ == "__main__":
    sys.exit(main())
