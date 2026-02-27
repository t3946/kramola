from typing import List

from services.loader_selenium import LoaderSelenium


URL_RUSSIAN = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-act"
URL_INTERNATIONAL = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-all"

URL_INTERNATIONAL_EXCLUDED = "https://www.fedsfm.ru/documents/omu-or-terrorists-catalog-excluded"
URL_RUSSIAN_EXCLUDED = "https://www.fedsfm.ru/documents/terrorists-catalog-portal-del"

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
            items.push({ name: currentName.trim(), birthDate: birthDate });
        }

        if (previousName) {
            items.push({ name: previousName.trim(), birthDate: null });
        }
    }

    return items;
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
            result: dict = {
                "international": {
                    "all": [],
                    "excluded": [],
                },
                "russian": {
                    "all": [],
                    "excluded": [],
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

            return result
        finally:
            self.loader.driver.quit()
