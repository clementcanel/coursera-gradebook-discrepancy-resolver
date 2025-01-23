from selenium.webdriver.common.by import By


class HomePage:
    login_selector = (By.XPATH, "//a[text()='Log In']")

    def __init__(self, driver):
        self.driver = driver

    def click_login(self):
        self.driver.find_element_by_xpath(*HomePage.login_selector).click()
