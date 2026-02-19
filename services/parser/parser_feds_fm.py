from typing import List

from services.loader_selenium import LoaderSelenium


URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"

JS_FIND_FL_NAMES = r"""
function findFLNames(selector) {
    const names = [];
    const elements = document.querySelectorAll(selector);
    const re = /\d+\.\s(.+?)\*?,\s*(\((.+?)\))?/;

    for (e of elements) {
        const matches = e.innerText.match(re) || [];
        const currentName = matches[1];
        const previousName = matches[3];

        if (currentName) {
            names.push(currentName);
        }

        if (previousName) {
            names.push(previousName);
        }
    }

    return names;
}

return findFLNames(arguments[0]);
"""

JS_FIND_UL_NAMES = r"""
function findULNames(selector) {
    const names = [];
    const elements = document.querySelectorAll(selector);

    for (e of elements) {
        let matches = e.innerText.match(/\d+\.\s([^*,\(]+)/);

        if (matches && matches[1]) {
            names.push(matches[1].trim());
        }

        matches = e.innerText.match(/\((.+?)\)/);

        if (matches) {
            const otherNames = matches[1]
                .split(';')
                .map(name => name.trim());
            names.push(...otherNames);
        }
    }

    return names;
}

return findULNames(arguments[0]);
"""


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

    def load(self) -> dict[str, dict[str, List[str]]]:
        try:
            result: dict[str, dict[str, List[str]]] = {}

            self.loader.get(URL_INTERNATIONAL)
            result["international"] = self._parse_catalog(
                "#russianFL ol.terrorist-list li",
                "#russianUL ol.terrorist-list li",
            )

            self.loader.get(URL_RUSSIAN)
            result["russian"] = self._parse_catalog(
                "#russianFL ol.terrorist-list li",
                "#russianUL ol.terrorist-list li",
            )

            return result
        finally:
            self.loader.driver.quit()
