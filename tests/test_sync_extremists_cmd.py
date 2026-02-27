from services.parser_feds_fm import ParserFedsFM


def test_parser() -> None:
    from app import app

    with app.app_context():
        ParserFedsFM().parse(download_new_data=False)
