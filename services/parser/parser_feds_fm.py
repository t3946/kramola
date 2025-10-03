from typing import List
from services.loader_selenium import LoaderSelenium


class ParserFedsFM:
    def __init__(self):
        self.loader = LoaderSelenium()

    def load(self) -> dict[str, List[str]]:
        try:
            self.loader.get("https://www.fedsfm.ru/documents/terrorists-catalog-portal-act")

            # [start] parse persons list
            js_find_fl_names = """
            function findFLNames() {
                const names = [];
                const elements = document.querySelectorAll('#russianFL ol.terrorist-list li');
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
            
            return findFLNames()
            """
            namesFL: List[str] = self.loader.driver.execute_script(js_find_fl_names)
            # [end]

            # [start] parse companies list
            js_find_ul_names = """
            function findULNames() {
                console.log('findULNames')
                const names = [];
                const elements = document.querySelectorAll('#russianUL ol.terrorist-list li');

                for (e of elements) {
                    //main name
                    let matches = e.innerText.match(/\d+\.\s([^*,\(]+)/);

                    if (matches && matches[1]) {
                        names.push(matches[1].trim());
                    }

                    //other names
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
            
            findULNames()

            return findULNames()
            """
            namesUL: List[str] = self.loader.driver.execute_script(js_find_ul_names)
            # [end]

            return {
                "namesFL": namesFL,
                "namesUL": namesUL,
            }
        finally:
            self.loader.driver.quit()
