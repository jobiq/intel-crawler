import random
import time

from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from scraper.helpers import Souped
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig
from scraper.exception import ScraperException


class CustomConfig(ScraperActionConfig):
    timeout: float
    verify_element: str


class CloudflareHuman(ScraperAction[CustomConfig]):
    uid = "jobiq.selenium.cloudflare_human"

    def verify_success(self, driver: Chrome, timeout: float | None = None):
        if timeout is None:
            timeout = self.config["timeout"] if "timeout" in self.config and self.config["timeout"] > 0 else 8

        # got throug each key of self.shared_config["domains"] and see if matches current driver ur
        # if not, then we are not on the right page
        found = False
        url = driver.current_url
        print(url)
        for domain in self.shared_config["domains"]:
            if domain in url:
                found = True

                # it may not be available
                na_text = self.shared_config["domains"][domain]["config"]["na"]
                if na_text:
                    try:
                        driver.find_element(By.XPATH, f"//*[contains(text(), '{na_text}')]")
                        raise ScraperException("error", "404 - Job No Longer available" )
                    except Exception:
                        pass

                # check if we are on the right page
                
                for key in self.shared_config["domains"][domain]:
                    if key != "config":
                        WebDriverWait(driver, timeout).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, self.shared_config["domains"][domain][key]))
                        )

                return
        
        if not found:
            raise ScraperException(
                "error", f"Could not bypass Cloudflare: {driver.current_url} not in {self.shared_config['domains']}")

    async def init(self):
        self.timeout = self.config["timeout"] if "timeout" in self.config and self.config["timeout"] > 0 else 8

    def try_open_tab(self, scraper: ScraperItem, sleep_before: float, sleep_after: float):
        
        driver = scraper.app.selenium.driver
        time.sleep(sleep_before)
        driver.execute_script(
            f'''window.open("{scraper.url}","_blank");''')  # open page in new tab
        time.sleep(sleep_after)

        # h = driver.window_handles[len(driver.window_handles) - 1]
        # driver.switch_to.window(window_name=h)

        self.verify_success(driver)
        scraper.soup = Souped(BeautifulSoup(
            driver.page_source, "html.parser"))

    async def _execute(self, scraper: ScraperItem):
        driver = scraper.app.selenium.driver

        sleep_before = 1 + random.random()
        sleep_after = 4 + 2 * random.random()

        # maybe we successfully loaded the page
        try:
            self.verify_success(driver, 0.5)
            scraper.soup = Souped(BeautifulSoup(
                driver.page_source, "html.parser"))
        except ScraperException as ex:
            raise ex
        except:
            try:
                self.try_open_tab(scraper, sleep_before, sleep_after)
            except:
                time.sleep(sleep_before)
                driver.execute_script(
                    f'''window.open("https://www.google.com","_blank");''')  # open page in new tab
                time.sleep(sleep_after)
                try:
                    print("retry 1")
                    self.try_open_tab(scraper, sleep_before, sleep_after)
                except:
                    time.sleep(sleep_before)
                    driver.execute_script(
                        f'''window.open("https://www.google.com?search=123","_blank");''')  # open page in new tab
                    time.sleep(sleep_after)
                    try:
                        print("retry 2")
                        self.try_open_tab(scraper, sleep_before, sleep_after)
                    except:
                        raise ScraperException(
                            "error", f"Could not bypass Cloudflare")

            finally:
                handle = driver.window_handles[len(driver.window_handles) - 1]

                # close all handles
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(
                        window_name=driver.window_handles[0])
                    driver.close()  # close first tab
                driver.switch_to.window(window_name=handle)

            # # driver.tab_new(scraper.url)
            # time.sleep(5)  # wait until page has loaded
            # # switch to first tab
            # driver.switch_to.window(window_name=driver.window_handles[0])
            # driver.close()  # close first tab
            # # switch back to new tab
            # driver.switch_to.window(window_name=driver.window_handles[0])
            # time.sleep(2)
            # driver.get("https://google.com")
            # time.sleep(2)
            # driver.get(scraper.url)  # this should pass cloudflare captchas now

            # try:
            #     self.verify_success(driver)
            #     scraper.soup = Souped(BeautifulSoup(
            #         driver.page_source, "html.parser"))
            #     return
            # except Exception as ex:
            #     try:
            #         element = driver.find_element(
            #             By.CSS_SELECTOR, 'input[value*="Verify"]'
            #         )
            #         element.click()
            #     except:

            #         # handle = driver.current_window_handle
            #         # driver.service.stop()
            #         # time.sleep(6)
            #         # selenium = Selenium()
            #         # selenium.init()
            #         # scraper.selenium = selenium

            #         # driver = selenium.driver
            #         # driver.switch_to.window(handle)

            #         # driver.refresh()
            #         # Store iframe web element
            #         iframe = driver.find_element(
            #             By.CSS_SELECTOR, 'iframe[title*="challenge"]')

            #         # switch to selected iframe
            #         driver.switch_to.frame(iframe)

            #         # Now click on button
            #         driver.find_element(
            #             By.CSS_SELECTOR, 'input[type="checkbox"]').click()

            #     try:
            #         self.verify_success(driver)
            #         scraper.soup = Souped(BeautifulSoup(
            #             driver.page_source, "html.parser"))
            #     except Exception as ex:
            #         raise Exception("error", f"Could not bypass Cloudflare")
