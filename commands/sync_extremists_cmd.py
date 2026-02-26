"""Flask CLI command: parse fedsfm.ru extremists catalogs and sync to extremists_terrorists table."""

from datetime import date, datetime

import click

from extensions import db
from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from models import ExtremistTerrorist
from services.parser.parser_feds_fm import ParserFedsFM


def _parse_birth_date(value: str | None) -> date | None:
    """Parse 'YYYY-MM-DD' string to date or None."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@click.command("extremists:parse")
def sync_extremists_cmd() -> None:
    """Parse international and russian catalogs from fedsfm.ru and sync to DB."""
    from app import app

    with app.app_context():
        parser = ParserFedsFM()
        data = parser.load()

        for area in ExtremistArea:
            block = data.get(area, {})
            items_fl = block.get("namesFL") or []
            names_ul = block.get("namesUL") or []

            ExtremistTerrorist.query.filter_by(area=area.value).delete(synchronize_session=False)

            for item in items_fl:
                name = item.get("name") if isinstance(item, dict) else item
                if not name or not str(name).strip():
                    continue
                name = str(name).strip()
                birth_date = _parse_birth_date(item.get("birthDate")) if isinstance(item, dict) else None
                row = ExtremistTerrorist(
                    full_name=name,
                    birth_date=birth_date,
                    search_terms=[name],
                    type=ExtremistStatus.FIZ.value,
                    area=area.value,
                )
                db.session.add(row)

            for name in names_ul:
                if not name or not str(name).strip():
                    continue
                row = ExtremistTerrorist(
                    full_name=name.strip(),
                    search_terms=[name.strip()],
                    type=ExtremistStatus.UR.value,
                    area=area.value,
                )
                db.session.add(row)

            db.session.commit()
            click.echo(f"Synced {area.value}: FL={len(items_fl)}, UL={len(names_ul)}")
