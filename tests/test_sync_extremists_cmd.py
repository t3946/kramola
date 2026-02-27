from services.parser import ParserFedsFM


def test_parser() -> None:
    from app import app

    with app.app_context():
        ParserFedsFM().parse()
