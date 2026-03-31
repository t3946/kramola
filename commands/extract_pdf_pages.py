#!/usr/bin/env python3
"""
Extracts a page range from a PDF file into a new PDF.
usage: python commands/extract_pdf_pages.py input.pdf output.pdf --start 1 --end 100
"""

import argparse
import logging
import sys
from pathlib import Path

import fitz

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "extract_pdf_pages.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def extract_pdf_pages(
    input_pdf_path: Path,
    output_pdf_path: Path,
    start_page: int,
    end_page: int,
) -> bool:
    """Extract pages from input PDF into output PDF."""
    source_pdf: fitz.Document = fitz.open(input_pdf_path)
    total_pages: int = len(source_pdf)

    if total_pages == 0:
        logger.error("Input PDF has no pages")
        source_pdf.close()
        return False

    if start_page < 1 or end_page < 1:
        logger.error("Page numbers must be greater than or equal to 1")
        source_pdf.close()
        return False

    if start_page > end_page:
        logger.error("Start page cannot be greater than end page")
        source_pdf.close()
        return False

    if start_page > total_pages:
        logger.error(
            "Start page is out of range: start=%s, total_pages=%s",
            start_page,
            total_pages,
        )
        source_pdf.close()
        return False

    validated_end_page: int = min(end_page, total_pages)

    if end_page > total_pages:
        logger.warning(
            "End page %s is out of range, using %s instead",
            end_page,
            validated_end_page,
        )

    target_pdf: fitz.Document = fitz.open()
    target_pdf.insert_pdf(
        source_pdf,
        from_page=start_page - 1,
        to_page=validated_end_page - 1,
    )

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    target_pdf.save(output_pdf_path)
    target_pdf.close()
    source_pdf.close()

    extracted_pages_count: int = validated_end_page - start_page + 1
    logger.info(
        "Extracted pages %s-%s (%s pages) to %s",
        start_page,
        validated_end_page,
        extracted_pages_count,
        output_pdf_path,
    )
    return True


def main() -> int:
    """Main entry point for extracting PDF page ranges."""
    parser = argparse.ArgumentParser(
        description="Extract a page range from PDF and save as a new PDF"
    )
    parser.add_argument("input", type=str, help="Path to input PDF file")
    parser.add_argument("output", type=str, help="Path to output PDF file")
    parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="First page number to extract (1-based, inclusive)",
    )
    parser.add_argument(
        "--end",
        type=int,
        required=True,
        help="Last page number to extract (1-based, inclusive)",
    )

    args = parser.parse_args()

    input_pdf_path: Path = Path(args.input).resolve()
    output_pdf_path: Path = Path(args.output).resolve()

    if not input_pdf_path.exists():
        logger.error("Input file not found: %s", input_pdf_path)
        return 1

    if input_pdf_path.suffix.lower() != ".pdf":
        logger.warning("Input file extension is not .pdf: %s", input_pdf_path.suffix)

    if extract_pdf_pages(
        input_pdf_path=input_pdf_path,
        output_pdf_path=output_pdf_path,
        start_page=args.start,
        end_page=args.end,
    ):
        logger.info("PDF extraction completed successfully")
        return 0

    logger.error("PDF extraction failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
