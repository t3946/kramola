from flask import current_app

from services import pymorphy_service
from services.fulltext_search import Phrase
from services.fulltext_search.strategies.surname_strategy.surname import Surname
from services.tokenization import Token


def test_surnames_comparison() -> None:
    from app import app

    with app.app_context():
        p1 = Phrase("опий")
        p2 = Phrase("опыт")

        current_app.logger.debug(p1)
        current_app.logger.debug(p2)

        p1 = Phrase("человек")
        p2 = Phrase("люди")

        current_app.logger.debug(p1)
        current_app.logger.debug(p2)