#!/usr/bin/env python3
"""
Loads extremists and terrorists list from file to MySQL.
"""

import sys
import logging
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists
from services.enum import PredefinedListKey
from services.utils.load_lines_from_txt import load_lines_from_txt

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "load_extremists_terrorists.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main function for loading extremists and terrorists list."""
    logger.info("=" * 60)
    logger.info("Starting loading extremists and terrorists list from file")
    logger.info("=" * 60)

    file_path = BASE_DIR / "predefined_lists" / f"{PredefinedListKey.EXTREMISTS_TERRORISTS.value}.txt"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    logger.info(f"Loading data from file: {file_path}")
    words_list = load_lines_from_txt(str(file_path))
    logger.info(f"Loaded {len(words_list)} words from file")

    if not words_list:
        logger.warning("No words loaded from file")
        return 1

    logger.info("Saving to MySQL...")
    lp = ListExtremistsTerrorists()
    lp.clear()
    lp.save(words_list, logging=True)
    logger.info(f"Saved {len(words_list)} words to MySQL")

    logger.info("=" * 60)
    logger.info("Loading completed successfully")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    from app import app

    with app.app_context():
        exit_code = main()
    sys.exit(exit_code)
