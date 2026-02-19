#!/usr/bin/env python3
"""
Loads extremists and terrorists list from file into extremists_terrorists table (russian area, status=fiz).
Main source is fedsfm.ru via flask extremists:sync.
"""

import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from extensions import db
from models import ExtremistTerrorist
from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from services.enum import PredefinedListKey
from services.utils.load_lines_from_txt import load_lines_from_txt

log_dir = BASE_DIR / "log"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "load_extremists_terrorists.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("=" * 60)
    logger.info("Loading extremists/terrorists from file into DB (russian, fiz)")
    logger.info("=" * 60)

    file_path = BASE_DIR / "predefined_lists" / f"{PredefinedListKey.EXTREMISTS_TERRORISTS.value}.txt"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    words_list = load_lines_from_txt(str(file_path))
    logger.info(f"Loaded {len(words_list)} lines from file")

    if not words_list:
        logger.warning("No lines loaded from file")
        return 1

    ExtremistTerrorist.query.filter_by(area=ExtremistArea.RUSSIAN.value).delete(synchronize_session=False)

    for line in words_list:
        name = (line or "").strip()
        if not name:
            continue
        row = ExtremistTerrorist(
            full_name=name,
            search_terms=[name],
            status=ExtremistStatus.FIZ.value,
            area=ExtremistArea.RUSSIAN.value,
        )
        db.session.add(row)

    db.session.commit()
    logger.info(f"Saved {len([l for l in words_list if (l or '').strip()])} rows to extremists_terrorists (russian)")

    logger.info("=" * 60)
    logger.info("Loading completed successfully")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    from app import app

    with app.app_context():
        exit_code = main()
    sys.exit(exit_code)
