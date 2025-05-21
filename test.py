from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-extensions')
options.add_argument('--start-maximized')
# options.add_argument('--headless')  # still needed for clean headless operation
options.binary_location = "/usr/bin/chromium"

driver = webdriver.Chrome(options=options)
driver.get("https://www.google.com")
print("Title is:", driver.title)
driver.quit()