import json
from pathlib import Path
from extensions import db
from typing import List, Dict, Tuple

from models.extremists_terrorists import ExtremistArea, ExtremistStatus, ExtremistTerrorist
from services.parser_feds_fm.process_raw import ProcessRaw
from services.parser_feds_fm.registry_loader import RegistryLoader

URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_RUSSIAN_EXCLUDED = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-del"

URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"
URL_INTERNATIONAL_EXCLUDED = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-excluded"






class ParserFedsFM (ProcessRaw):
    def __init__(self) -> None:
        pass


    def _load(self) -> dict:
        result: dict = {
            "international": {
                "all": {},
                "excluded": {},
            },
            "russian": {
                "all": {},
                "excluded": {},
            }
        }

        self.loader.get(URL_INTERNATIONAL)
        result["international"]['all'] = self._parse_catalog(
            "#russianFL ol.terrorist-list li",
            "#russianUL ol.terrorist-list li",
        )

        self.loader.get(URL_INTERNATIONAL_EXCLUDED)
        result["international"]['excluded'] = self._parse_catalog(
            "#russianFL ol.terrorist-list li",
            "#russianUL ol.terrorist-list li",
        )

        # [start] process raw international data
        for all_division in result["international"]['all']:
            for item in all_division["names_FL"]:
                item["sanction_code"] = _parse_sanction_code(item["text"])

            for item in all_division["names_UL"]:
                item["sanction_code"] = _parse_sanction_code(item["text"])

        for excluded_division in result["international"]['excluded']:
            for item in excluded_division["names_FL"]:
                item["sanction_code"] = _parse_sanction_code(item["text"])

            for item in excluded_division["names_UL"]:
                item["sanction_code"] = _parse_sanction_code(item["text"])
        # [end]

        self.loader.get(URL_RUSSIAN)
        result["russian"]['all'] = self._parse_catalog(
            "#russianFL ol.terrorist-list li",
            "#russianUL ol.terrorist-list li",
        )

        self.loader.get(URL_RUSSIAN_EXCLUDED)
        result["russian"]['excluded'] = self._parse_catalog(
            "#russianFL ol.terrorist-list li",
            "#russianUL ol.terrorist-list li",
        )

        self.loader.driver.quit()

        return result

    def sync_international_fl_ul(self, data_from_registry: dict) -> None:
        # [start] build models dict
        models: List[ExtremistTerrorist] = (
            ExtremistTerrorist
            .query
            .filter(ExtremistTerrorist.area == ExtremistArea.INTERNATIONAL.value)
            .all()
        )
        models_dict: Dict[Tuple[str, str], ExtremistTerrorist] = {}

        # key models by full_name and sanction_code
        for model in models:
            key: Tuple[str, str] = (model.full_name, model.sanction_code)
            models_dict[key] = model
        # [end]

        # [start] sync models with registry data
        for division_all in data_from_registry["all"]:
            for fl in division_all["namesFL"]:
                # todo check if models_dict contain this fl
                pass

            for ul in division_all["namesUL"]:
                pass
        # [end]

        pass

    def parse(self, download_new_data: bool = True) -> None:
        # download new raw data
        if download_new_data:
            RegistryLoader().load()

        # [start] read raw data
        raw_data_path: Path = RegistryLoader.get_raw_path()

        if not raw_data_path.is_file():
            raise FileNotFoundError(
                f"Raw data file not found, you should download it from feds fm first: {raw_data_path.absolute()}"
            )

        raw_data: dict = json.loads(raw_data_path.read_text(encoding="utf-8"))
        # [end]

        # [start] process raw data to rich data objects
        # international all FL/UL: raw + sanction_code; russian FL: raw + birth_date; russian UL: raw only
        rich_data: List[dict] = []

        rich_data.extend([{"raw": s, "type": ExtremistStatus.FIZ, "area": ExtremistArea.INTERNATIONAL, "is_active": True} for s in raw_data["international"]["all"]["namesFL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.UR, "area": ExtremistArea.INTERNATIONAL, "is_active": True} for s in raw_data["international"]["all"]["namesUL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.FIZ, "area": ExtremistArea.INTERNATIONAL, "is_active": False} for s in raw_data["international"]["excluded"]["namesFL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.UR, "area": ExtremistArea.INTERNATIONAL, "is_active": False} for s in raw_data["international"]["excluded"]["namesUL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.FIZ, "area": ExtremistArea.RUSSIAN, "is_active": True} for s in raw_data["russian"]["all"]["namesFL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.UR, "area": ExtremistArea.RUSSIAN, "is_active": True} for s in raw_data["russian"]["all"]["namesUL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.FIZ, "area": ExtremistArea.RUSSIAN, "is_active": False} for s in raw_data["russian"]["excluded"]["namesFL"]])
        rich_data.extend([{"raw": s, "type": ExtremistStatus.UR, "area": ExtremistArea.RUSSIAN, "is_active": False} for s in raw_data["russian"]["excluded"]["namesUL"]])
        # [end]

        # [start] hydrate rich data objects
        for item in rich_data:
            if item["area"] == ExtremistArea.INTERNATIONAL:
                item["sanction_code"] = self._parse_sanction_code(item["raw"])

            if item["area"] == ExtremistArea.RUSSIAN and item["type"] == ExtremistStatus.FIZ:
                item["birth_date"] = self._parse_birthdate(item["raw"])
                item["names"] = self._parse_ru_fl_name(item["raw"])
        # [end]

        return
        data = self._load()

        # new sync logic
        self.sync_international_fl_ul(data["international"])

        # old sync logic
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
            print(f"Synced {area.value}: FL={len(items_fl)}, UL={len(names_ul)}")
