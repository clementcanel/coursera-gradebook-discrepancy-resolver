from selenium.webdriver.common.by import By
from grade_verification.page_objects.base_page import BasePage


class HomePage(BasePage):
    LOGIN_SELECTOR = (By.CSS_SELECTOR, "a[data-e2e='header-login-button']")
    PROFILE_DROPDOWN_SELECTOR = (By.CSS_SELECTOR, "div#authenticated-info-menu")

    def is_logged_in(self) -> bool:
        # check if the profile dropdown is visible
        return self.is_element_visible(self.PROFILE_DROPDOWN_SELECTOR, timeout=5)

    def click_login(self):
        # click the 'Log In' button on the homepage
        self.click(self.LOGIN_SELECTOR)
