from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage

class HomePage(BasePage):
    LOGIN_SELECTOR = (By.CSS_SELECTOR, "a[data-e2e='header-login-button']")
    PROFILE_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'button[data-e2e="header-profile"]')
    ADMIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'a[href="/admin/"]')

    def is_logged_in(self) -> bool:
        return self.is_element_present(self.PROFILE_BUTTON_SELECTOR, timeout=5)

    def click_login(self):
        self.click(self.LOGIN_SELECTOR)

