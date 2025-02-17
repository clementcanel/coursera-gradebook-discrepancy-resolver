from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage

class HomePage(BasePage):
    LOGIN_SELECTOR = (By.CSS_SELECTOR, "a[data-e2e='header-login-button']")
    PROFILE_ICON_IDENTIFIER = (By.CSS_SELECTOR, "div#authenticated-info-menu")
    PROFILE_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'button[data-e2e="header-profile"]')
    ADMIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'a[href="/admin/"]')

    def is_logged_in(self) -> bool:
        return self.is_element_present(self.PROFILE_ICON_IDENTIFIER, timeout=5)

    def click_login(self):
        self.click(self.LOGIN_SELECTOR)

    def scrape_courses(self):
        """clicks the profile button and then the 'educator admin' link using explicit waits"""
        
        # click the profile button
        self.click(self.PROFILE_BUTTON_SELECTOR)
        # wait until the admin link is clickable
        WebDriverWait(self.driver, 5, poll_frequency=0.5).until(
            EC.element_to_be_clickable(self.ADMIN_BUTTON_SELECTOR)
        )
        self.click(self.ADMIN_BUTTON_SELECTOR)

        return
