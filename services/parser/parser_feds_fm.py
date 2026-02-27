import re
from datetime import date, datetime
from services.loader_selenium import LoaderSelenium
from extensions import db
from typing import List, Union, Dict, Tuple

from models.extremists_terrorists import ExtremistArea, ExtremistStatus, ExtremistTerrorist

URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_RUSSIAN_EXCLUDED = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-del"

URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"
URL_INTERNATIONAL_EXCLUDED = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-excluded"

JS_FIND_FL_NAMES = r"""
function parseBirthDate(text) {
    const birthRe = /(\d{1,2})\.(\d{1,2})\.(\d{4})\s+г\.р\./;
    const m = (text || "").match(birthRe);
    if (!m) return null;
    const d = m[1].padStart(2, '0');
    const month = m[2].padStart(2, '0');
    const y = m[3];
    return y + '-' + month + '-' + d;
}

function findFLNames(selector) {
    const items = [];
    const elements = document.querySelectorAll(selector);
    const nameRe = /\d+\.\s(.+?)\*?,\s*(\((.+?)\))?/;

    for (e of elements) {
        const text = e.innerText;
        const nameMatch = text.match(nameRe) || [];
        const currentName = nameMatch[1];
        const previousName = nameMatch[3];
        const birthDate = parseBirthDate(text);

        if (currentName) {
            items.push({
                name: currentName.trim(),
                birthDate: birthDate,
                text: text,
            });
        }

        if (previousName) {
            items.push({
                name: previousName.trim(),
                birthDate: null,
                text: text,
            });
        }
    }

    return items;
}

return findFLNames(arguments[0]);
"""

JS_FIND_UL_NAMES = r"""
function findULNames(selector) {
    const items = [];
    const elements = document.querySelectorAll(selector);

    for (e of elements) {
        items.push({
            text: e.innerText,
        });
    }

    return items;
}

return findULNames(arguments[0]);
"""


def _parse_birth_date(value: Union[str, None]) -> Union[date, None]:
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


def _parse_sanction_code(text) -> Union[str, None]:
    """
    extract sanction code from text and return None if no sanction code(ex. QDi.289, TAi.155, IRi.001, QDi.1234)
    """
    pattern = r'(?!код\s+санкций\s+ООН:\s+)(\w+?\.\d+)'
    match = re.search(pattern, text, re.IGNORECASE)

    return match.group(0) if match else None


class ParserFedsFM:
    def __init__(self) -> None:
        self.loader = LoaderSelenium()

    def _parse_catalog(
            self,
            fl_selector: str,
            ul_selector: str,
    ) -> dict[str, List[str]]:
        names_fl: List[str] = self.loader.driver.execute_script(JS_FIND_FL_NAMES, fl_selector)
        names_ul: List[str] = self.loader.driver.execute_script(JS_FIND_UL_NAMES, ul_selector)

        return {"namesFL": names_fl or [], "namesUL": names_ul or []}

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

    def parse(self):
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
