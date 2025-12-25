#!/usr/bin/env python3
"""
Loads prohibited substances list from file to Redis.
"""

import sys
import logging
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.words_list.list_prohibited_substances import ListProhibitedSubstances
from services.words_list import PredefinedListKey
from services.utils.load_lines_from_txt import load_lines_from_txt

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "load_prohibited_substances.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function for loading prohibited substances list."""
    try:
        logger.info("=" * 60)
        logger.info("Starting loading prohibited substances list from file")
        logger.info("=" * 60)

        # File path
        file_path = BASE_DIR / "predefined_lists" / f"{PredefinedListKey.PROHIBITED_SUBSTANCES.value}.txt"
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 1

        # Load data from file
        logger.info(f"Loading data from file: {file_path}")
        words_list = load_lines_from_txt(str(file_path))
        logger.info(f"Loaded {len(words_list)} words from file")

        if not words_list:
            logger.warning("No words loaded from file")
            return 1

        # Save to Redis
        logger.info("Saving to Redis...")
        lp = ListProhibitedSubstances()
        lp.clear()
        lp.save(words_list, logging=True)
        logger.info(f"Saved {len(words_list)} words to Redis")

        logger.info("=" * 60)
        logger.info("Loading completed successfully")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR during loading: {e}", exc_info=True)
        logger.error("=" * 60)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

