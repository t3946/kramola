#!/usr/bin/env python3
"""
Converts DOCX file to PDF format.
usage: python commands/convert_docx_to_pdf.py input.docx output.pdf
"""

import sys
import logging
import argparse
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "convert_docx_to_pdf.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Convert DOCX file to PDF.
    
    Args:
        docx_path: Path to input DOCX file
        pdf_path: Path to output PDF file
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        from docx2pdf import convert
        
        logger.info(f"Converting DOCX to PDF: {docx_path} -> {pdf_path}")
        convert(docx_path, pdf_path)
        logger.info(f"Successfully converted to: {pdf_path}")
        return True
        
    except ImportError:
        logger.error("docx2pdf library not installed. Install with: pip install docx2pdf")
        logger.error("Note: docx2pdf requires LibreOffice or Microsoft Word to be installed")
        return False
    except Exception as e:
        logger.error(f"Error during conversion: {e}", exc_info=True)
        return False


def main() -> int:
    """Main function for converting DOCX to PDF."""
    parser = argparse.ArgumentParser(description='Convert DOCX file to PDF')
    parser.add_argument('input', type=str, help='Path to input DOCX file')
    parser.add_argument('output', type=str, nargs='?', help='Path to output PDF file (optional)')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("Starting DOCX to PDF conversion")
        logger.info("=" * 60)
        
        docx_path = Path(args.input).resolve()
        
        if not docx_path.exists():
            logger.error(f"Input file not found: {docx_path}")
            return 1
        
        if not docx_path.suffix.lower() == '.docx':
            logger.warning(f"File extension is not .docx: {docx_path.suffix}")
        
        if args.output:
            pdf_path = Path(args.output).resolve()
        else:
            pdf_path = docx_path.with_suffix('.pdf')
        
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        if convert_docx_to_pdf(str(docx_path), str(pdf_path)):
            logger.info("=" * 60)
            logger.info("Conversion completed successfully")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("=" * 60)
            logger.error("Conversion failed")
            logger.error("=" * 60)
            return 1
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR during conversion: {e}", exc_info=True)
        logger.error("=" * 60)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

