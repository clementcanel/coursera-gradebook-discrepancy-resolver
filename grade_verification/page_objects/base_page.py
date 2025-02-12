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
        # navigate the browser to a URL
        self.driver.get(url)

    """
        click an element by a locator (by, value) tuple
        example:
            self.click((By.CSS_SELECTOR, "#some-button"))
    """
    def click(self, locator: tuple, timeout=10):
        
        WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator),
            message=f"Element {locator} not clickable within {timeout}s"
        )
        self.driver.find_element(*locator).click()

    def js_click(self, locator: tuple, timeout=20):
        """
        locates an element by 'presence_of_element_located',
        then clicks it via JavaScript execution
        """
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].click();", element)

    """
        type text into an input specified by a locator (by, value) tuple
        example:
            self.type((By.NAME, "email"), "my_email@example.com")
    """
    def type(self, locator: tuple, text: str, clear_first=True, timeout=10):
        
        elem = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator),
            message=f"Element {locator} not visible within {timeout}s"
        )
        if clear_first:
            elem.clear()
        elem.send_keys(text)

    """
        return True if the element is present within `timeout` seconds or else False
    """
    def is_element_present(self, locator: tuple, timeout=10) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except:
            return False
    """
        simple hard sleep
    """
    def sleep(self, seconds: int):
       
        time.sleep(seconds)