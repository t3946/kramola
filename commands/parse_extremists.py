"""Flask CLI command: parse fedsfm.ru extremists catalogs and sync to extremists_terrorists table."""
import click

from services.parser.parser_feds_fm import ParserFedsFM

@click.command("extremists:parse")
def sync_extremists_cmd() -> None:
    """Parse international and russian catalogs from fedsfm.ru and sync to DB."""
    from app import app

    with app.app_context():
        ParserFedsFM().parse()
