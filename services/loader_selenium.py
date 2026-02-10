import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class LoaderSelenium:
    def __init__(
        self,
        headless: bool = True,
        use_local_chrome: bool = False,  # False = browser in Docker. True = local Chrome (window on this machine).
    ) -> None:
        # headless=False only useful when use_local_chrome=True (with Remote, browser has no visible window anyway).
        chrome_options = Options()

        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")

        if use_local_chrome:
            self.driver = webdriver.Chrome(options=chrome_options)
        else:
            executor = os.environ.get("SELENIUM_URL", "http://localhost:4444/wd/hub")
            self.driver = webdriver.Remote(command_executor=executor, options=chrome_options)

    def get(self, url: str) -> None:
        self.driver.get(url)

    def find_elements(self, selector: str):
        return self.driver.find_elements(By.CSS_SELECTOR, selector)
