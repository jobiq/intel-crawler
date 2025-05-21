

# from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# import chromedriver_autoinstaller  # type: ignore


class Selenium:
    def __init__(self):
        self.initialised = None

    def init(self):
        # import chromedriver_autoinstall  # type:ignore
        import undetected_chromedriver as uc # type:ignore
        
        # chromedriver_autoinstall.install()

        # windows_useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
        # linux_useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"

        options = Options()
        options = uc.ChromeOptions()
        # options.headless = True

        # options.add_argument("start-maximized")
        # options.add_experimental_option(
        #     "excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)

        options.add_argument("--disable-popup-blocking")
        options.binary_location = "/usr/bin/chromium"
        # # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')

        # options.add_argument(f"user-agent={linux_useragent}")
        # options.add_argument("--disable-web-security")
        # options.add_argument("--disable-xss-auditor")
        # options.add_argument("--disable-blink-features=AutomationControlled")

        # platform = {
        #     "windows": "Win32",
        #     "linux": "Linux x86_64"
        # }

        self.driver = uc.Chrome(options=options)
        # self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        #                             "userAgent": linux_useragent})
        # self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        #     "source": """
        #         Object.defineProperty(navigator, 'webdriver', {
        #             get: () => undefined
        #         }),
        #         Object.defineProperty(navigator, 'languages', {
        #             get: () => ['en-US', 'en']
        #         }),
        #         Object.defineProperty(navigator, 'platform', {
        #             get: () => 'Linux x86_64'
        #         })
        #     """
        # })

        self.initialised = True

    def load_page(self, url: str, wait_css_selector: str | None = None, wait_xpath: str | None = None):
        if not self.initialised:
            self.init()

        self.page = self.driver.get(url)

        if wait_css_selector is not None:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, wait_css_selector))
            )

        if wait_xpath is not None:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, wait_xpath))
            )

        html = self.driver.page_source

        return html

        # self.soup = BeautifulSoup(html, "html.parser")
        # return self.soup

    def quit(self):
        if (self.initialised):
            self.driver.quit()
