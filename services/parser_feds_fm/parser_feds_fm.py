import json
from pathlib import Path
from extensions import db
from typing import List, Dict, Tuple

from models.extremists_terrorists import ExtremistArea, ExtremistStatus, ExtremistTerrorist
from services.parser_feds_fm.registry_loader import RegistryLoader
from services.parser_feds_fm.process_raw_international import ProcessRawInternational
from services.parser_feds_fm.process_raw_russian import ProcessRawRussian

URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_RUSSIAN_EXCLUDED = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-del"

URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"
URL_INTERNATIONAL_EXCLUDED = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-excluded"


class ParserFedsFM(ProcessRawInternational, ProcessRawRussian):
    def __init__(self) -> None:
        pass

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
                item["names"] = self._parse_international_name(item["raw"])

            if item["area"] == ExtremistArea.RUSSIAN:
                if item["type"] == ExtremistStatus.FIZ:
                    item["birth_date"] = self._parse_birthdate(item["raw"])
                    item["names"] = self._parse_ru_fl_name(item["raw"])

                if item["type"] == ExtremistStatus.UR:
                    item["names"] = self._parse_ru_ul_name(item["raw"])

            item["search_terms"] = []

            if item["names"]["main"]:
                item["full_name"] = item["names"]["main"]
                item["search_terms"].append(item["names"]["main"])

            if item["names"]["additional"]:
                item["search_terms"].extend(item["names"]["additional"])
        # [end]

        # [start] sync DB data
        international_items = [item for item in rich_data if item["area"] == ExtremistArea.INTERNATIONAL]

        for item in international_items:
            old_model = (
                ExtremistTerrorist
                .query
                .filter(ExtremistTerrorist.area == ExtremistArea.INTERNATIONAL.value)
                .filter(ExtremistTerrorist.sanction_code == item.get("sanction_code"))
                .first()
            )

            new_model = ExtremistTerrorist(
                raw_source=item.get("raw"),
                full_name=item.get("full_name"),
                search_terms=item.get("search_terms"),
                type=item["type"].value,
                area=ExtremistArea.INTERNATIONAL.value,
                sanction_code=item.get("sanction_code"),
                is_active=item["is_active"],
            )

            # insert new
            if old_model is None:
                db.session.add(new_model)
            elif old_model.is_active != new_model.is_active:
                old_model.is_active = new_model.is_active
        # [end]
        return
