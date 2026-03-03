import json
import time
from pathlib import Path
from extensions import db
from typing import List, Dict, Tuple

from models.extremists_terrorists import ExtremistArea, ExtremistType, ExtremistTerrorist
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

    def parse(self, download_new_data: bool = True) -> None:
        print("Parse: start")

        # download new raw data
        if download_new_data:
            print("Parse: downloading new data")
            RegistryLoader().load()
            print("Parse: data loaded")
        else:
            print("Parse: read old data")

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

        rich_data.extend(
            [{"raw": s, "type": ExtremistType.FIZ, "area": ExtremistArea.INTERNATIONAL, "is_active": True} for s in
             raw_data["international"]["all"]["namesFL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.UR, "area": ExtremistArea.INTERNATIONAL, "is_active": True} for s in
             raw_data["international"]["all"]["namesUL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.FIZ, "area": ExtremistArea.INTERNATIONAL, "is_active": False} for s in
             raw_data["international"]["excluded"]["namesFL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.UR, "area": ExtremistArea.INTERNATIONAL, "is_active": False} for s in
             raw_data["international"]["excluded"]["namesUL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.FIZ, "area": ExtremistArea.RUSSIAN, "is_active": True} for s in
             raw_data["russian"]["all"]["namesFL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.UR, "area": ExtremistArea.RUSSIAN, "is_active": True} for s in
             raw_data["russian"]["all"]["namesUL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.FIZ, "area": ExtremistArea.RUSSIAN, "is_active": False} for s in
             raw_data["russian"]["excluded"]["namesFL"]])
        rich_data.extend(
            [{"raw": s, "type": ExtremistType.UR, "area": ExtremistArea.RUSSIAN, "is_active": False} for s in
             raw_data["russian"]["excluded"]["namesUL"]])
        # [end]

        # [start] hydrate rich data objects
        for item in rich_data:
            item["raw"] = self._strip_number(item["raw"])

            if item["area"] == ExtremistArea.INTERNATIONAL:
                item["sanction_code"] = self._parse_sanction_code(item["raw"])

                if item["type"] == ExtremistType.FIZ:
                    item["names"] = self._parse_international_fl_name(item["raw"])

                if item["type"] == ExtremistType.UR:
                    item["names"] = self._parse_international_ul_name(item["raw"])

            if item["area"] == ExtremistArea.RUSSIAN:
                if item["type"] == ExtremistType.FIZ:
                    birth = self._parse_birth_details(item["raw"])
                    item["birth_date"] = birth["date"]
                    item["birth_place"] = birth["place"]
                    item["names"] = self._parse_ru_fl_name(item["raw"])

                if item["type"] == ExtremistType.UR:
                    item["names"] = self._parse_ru_ul_name(item["raw"])

            item["search_terms"] = []

            if item["names"]["main"]:
                item["full_name"] = item["names"]["main"]
                item["search_terms"].append(item["names"]["main"])

            additional = item["names"].get("additional") or []

            if additional:
                item["search_terms"].extend(additional)
        # [end]

        # [start] sync DB international data
        international_items = [item for item in rich_data if item["area"] == ExtremistArea.INTERNATIONAL]
        commit_step = 1000
        print(f"Sync international: start ({len(international_items)} items)")
        international_start = time.perf_counter()

        for i, item in enumerate(international_items):
            query = (
                ExtremistTerrorist
                .query
                .filter(ExtremistTerrorist.area == ExtremistArea.INTERNATIONAL.value)
                .filter(ExtremistTerrorist.sanction_code == item["sanction_code"])
            )

            if item["names"]["main"]:
                query = query.filter(ExtremistTerrorist.full_name == item["names"]["main"])
            else:
                query = query.filter(ExtremistTerrorist.raw_source == item["raw"])

            old_model = query.first()

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

            if i % commit_step == 0:
                db.session.commit()
                elapsed = time.perf_counter() - international_start
                print(f"\r{i}/{len(international_items)} items processed ({elapsed:.1f}s)", end="", flush=i > 0)

        if len(international_items): print("")
        print(f"Sync international: done ({len(international_items)} items)")
        # [end]

        # [start] sync DB russian data
        russian_items = [item for item in rich_data if item["area"] == ExtremistArea.RUSSIAN]
        print(f"Sync russian: start ({len(russian_items)} items)")
        russian_start = time.perf_counter()

        for i, item in enumerate(russian_items):
            query = (
                ExtremistTerrorist
                .query
                .filter(ExtremistTerrorist.area == ExtremistArea.RUSSIAN.value)
                .filter(ExtremistTerrorist.type == item["type"].value)
            )

            if item["names"]["main"]:
                query = query.filter(ExtremistTerrorist.full_name == item["names"]["main"])
            else:
                query = query.filter(ExtremistTerrorist.raw_source == item["raw"])

            old_model = None
            new_model = ExtremistTerrorist(
                raw_source=item.get("raw"),
                full_name=item.get("full_name"),
                search_terms=item.get("search_terms"),
                type=item["type"].value,
                area=ExtremistArea.RUSSIAN.value,
                is_active=item["is_active"],
            )

            if item["type"] == ExtremistType.FIZ:
                old_model = (
                    query
                    .filter(ExtremistTerrorist.birth_date == item["birth_date"])
                    .filter(ExtremistTerrorist.birth_place == item["birth_place"])
                    .first()
                )

                new_model.birth_date = item["birth_date"]
                new_model.birth_place = item["birth_place"]

            if item["type"] == ExtremistType.UR:
                old_model = query.first()

            if old_model is None:
                db.session.add(new_model)
            else:
                old_model.is_active = new_model.is_active

            if i % commit_step == 0:
                db.session.commit()
                elapsed = time.perf_counter() - russian_start
                print(f"\r{i}/{len(russian_items)} items processed ({elapsed:.1f}s)", end="", flush=i > 0)

        if len(russian_items): print("")
        print(f"Sync russian: done ({len(russian_items)} items)")
        # [end]

        db.session.commit()
        print("Parse: Done!")
        return
