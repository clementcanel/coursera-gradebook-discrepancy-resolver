from selenium.webdriver.common.by import By
from grade_verification.page_objects.base_page import BasePage


class HomePage(BasePage):
    LOGIN_SELECTOR = (By.CSS_SELECTOR, "a[data-e2e='header-login-button']")
    PROFILE_ICON_IDENTIFIER = (By.CSS_SELECTOR, "div#authenticated-info-menu")
    PROFILE_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'button[data-e2e="header-profile"]')
    ADMIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'a[href="/admin/"]')

    def is_logged_in(self) -> bool:
        # check if the profile dropdown is visible
        return self.is_element_present(self.PROFILE_ICON_IDENTIFIER, timeout=5)

    def click_login(self):
        # click the 'Log In' button on the homepage
        self.js_click(self.LOGIN_SELECTOR)

    def nav_to_courses(self):
        # click the profile button in the header (via JS)
        self.js_click(self.PROFILE_BUTTON_SELECTOR)
        self.sleep(2)  # wait a moment for dropdown to appear

        # click the "Educator Admin" link (via JS)
        self.js_click(self.ADMIN_BUTTON_SELECTOR)
        self.sleep(2)
