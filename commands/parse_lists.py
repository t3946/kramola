#!/usr/bin/env python3
"""
Runs from cron to update lists of individuals and legal entities.
"""

import sys
import logging
from pathlib import Path

# Add project root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.parser.parser_feds_fm import ParserFedsFM

# Configure logging
log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)

log_file = log_dir / "parse_lists.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8')],
)

logger = logging.getLogger(__name__)


def main():
    """Main function for parsing execution."""
    try:
        logger.info("=" * 60)
        logger.info("Starting parsing lists from fedsfm.ru")
        logger.info("=" * 60)

        # Initialize parser
        logger.info("Initializing parser...")
        parser = ParserFedsFM()

        # Load data (extremists: use flask extremists:sync; FL/UL: inagents pipeline)
        logger.info("Loading data from website...")
        data = parser.load()
        for area_key in ("international", "russian"):
            block = data.get(area_key) or {}
            logger.info(
                f"Records {area_key}: FL - {len(block.get('namesFL') or [])}, UL - {len(block.get('namesUL') or [])}"
            )

        logger.info("=" * 60)
        logger.info("Parsing completed successfully")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"ERROR during parsing execution: {e}", exc_info=True)
        logger.error("=" * 60)
        return 1


if __name__ == '__main__':
    from app import app

    with app.app_context():
        exit_code = main()
    sys.exit(exit_code)
