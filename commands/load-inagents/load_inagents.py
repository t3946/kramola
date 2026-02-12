"""Open minjust registry page in Selenium, get export link via getLink.js, download xlsx to temp."""

import ssl
from pathlib import Path
from urllib.request import Request, urlopen
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from services.loader_selenium import LoaderSelenium

REGISTRY_URL = "https://minjust.gov.ru/ru/pages/reestr-inostryannykh-agentov/#"


def _read_get_link_script() -> str:
    path = Path(__file__).parent / "getLink.js"
    return path.read_text(encoding="utf-8")


def _get_export_link(driver: WebDriver) -> str | None:
    script = _read_get_link_script()
    result = driver.execute_script(script)
    if result is None or not result.strip():
        return None
    return result.strip()


def _download_xlsx(export_url: str, driver: WebDriver, save_dir: Path) -> Path:
    cookies = driver.get_cookies()
    cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    req = Request(export_url, headers={"Cookie": cookie_header})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urlopen(req, context=ctx) as resp:
        content = resp.read()
    disposition = resp.headers.get("Content-Disposition")
    if disposition and "filename=" in disposition:
        name = disposition.split("filename=")[-1].strip('"\'')
    else:
        name = "reestr-inostrannykh-agentov.xlsx"
    out_path = save_dir / name
    out_path.write_bytes(content)
    return out_path


def run() -> Path | None:
    """Open registry page, run getLink.js, download xlsx if link present. Returns path to xlsx or None."""
    loader = LoaderSelenium()
    driver = loader.driver
    loader.get(REGISTRY_URL)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    export_link = _get_export_link(driver)
    if export_link is None:
        driver.quit()
        return None
    temp_dir = Path(__file__).parent / "temp"
    out_path = _download_xlsx(export_link, driver, temp_dir)
    driver.quit()
    return out_path


class InagentsXlsxParser:
    """Parser for downloaded foreign agents registry xlsx. Left empty for future implementation."""

    pass


if __name__ == "__main__":
    run()
