"""Flask CLI command: parse fedsfm.ru extremists catalogs and sync to extremists_terrorists table."""

import click

from extensions import db
from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from models import ExtremistTerrorist
from services.parser.parser_feds_fm import ParserFedsFM


@click.command("extremists:sync")
def sync_extremists_cmd() -> None:
    """Parse international and russian catalogs from fedsfm.ru and sync to DB."""
    from app import app

    with app.app_context():
        parser = ParserFedsFM()
        data = parser.load()

        for area_key, area_enum in [("international", ExtremistArea.INTERNATIONAL), ("russian", ExtremistArea.RUSSIAN)]:
            block = data.get(area_key, {})
            names_fl = block.get("namesFL") or []
            names_ul = block.get("namesUL") or []

            ExtremistTerrorist.query.filter_by(area=area_enum.value).delete(synchronize_session=False)

            for name in names_fl:
                if not name or not str(name).strip():
                    continue
                row = ExtremistTerrorist(
                    full_name=name.strip(),
                    search_terms=[name.strip()],
                    type=ExtremistStatus.FIZ.value,
                    area=area_enum.value,
                )
                db.session.add(row)

            for name in names_ul:
                if not name or not str(name).strip():
                    continue
                row = ExtremistTerrorist(
                    full_name=name.strip(),
                    search_terms=[name.strip()],
                    type=ExtremistStatus.UR.value,
                    area=area_enum.value,
                )
                db.session.add(row)

            db.session.commit()
            click.echo(f"Synced {area_key}: FL={len(names_fl)}, UL={len(names_ul)}")
