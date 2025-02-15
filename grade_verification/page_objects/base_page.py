import time
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(self.driver)
    
    def open(self, url: str):
        # Navigate the browser to a URL
        self.driver.get(url)

    def click(self, locator: tuple, timeout=10):
        """Waits until the element is clickable and then clicks it."""
        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.element_to_be_clickable(locator),
            message=f"Element {locator} not clickable within {timeout}s"
        )
        element.click()

    def js_click(self, locator: tuple, timeout=8):
        """Waits until the element is present and then clicks it using JavaScript."""
        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].click();", element)

    def type(self, locator: tuple, text: str, clear_first=True, timeout=10):
        """Waits until the element is visible and then types text into it."""
        elem = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.visibility_of_element_located(locator),
            message=f"Element {locator} not visible within {timeout}s"
        )
        if clear_first:
            elem.clear()
        elem.send_keys(text)

    def is_element_present(self, locator: tuple, timeout=10) -> bool:
        """Returns True if the element is present (within the timeout), else False."""
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def sleep(self, seconds: int):
        """Minimal sleep function; use explicit waits instead whenever possible."""
        time.sleep(seconds)