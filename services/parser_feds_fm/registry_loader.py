import json
from pathlib import Path
from typing import List

from services.loader_selenium import LoaderSelenium
from services.utils.get_project_root import get_project_root

URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_RUSSIAN_EXCLUDED = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-del"

URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"
URL_INTERNATIONAL_EXCLUDED = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-excluded"

JS_PARSE_LIST = r"""
function findULNames(selector) {
    const items = [];
    const elements = document.querySelectorAll(selector);

    for (e of elements) {
        items.push(e.innerText);
    }

    return items;
}

return findULNames(arguments[0]);
"""


class RegistryLoader:
    def __init__(self) -> None:
        self.loader = LoaderSelenium()

    @staticmethod
    def get_raw_path() -> Path:
        return get_project_root() / "temp" / "feds_fm_parser" / "raw.json"

    def _parse_catalog(
            self,
            fl_selector: str,
            ul_selector: str,
    ) -> dict[str, List[str]]:
        return {
            "namesFL": self.loader.driver.execute_script(JS_PARSE_LIST, fl_selector) or [],
            "namesUL": self.loader.driver.execute_script(JS_PARSE_LIST, ul_selector) or []
        }

    def load(self):
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

        out_path: Path = self.get_raw_path()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
