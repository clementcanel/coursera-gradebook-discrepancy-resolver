from selenium.webdriver.common.by import By
from grade_verification.page_objects.base_page import BasePage

class LoginPage(BasePage):
    USERNAME_FIELD = (By.NAME, "email")
    PASSWORD_FIELD = (By.NAME, "password")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[data-e2e='login-form-submit-button']")
    
    """
        fill in the username, fill in the password, and click Submit

    """
    def login(self, username: str, password: str):
        
        self.type(self.USERNAME_FIELD, username)
        self.type(self.PASSWORD_FIELD, password)
        self.click(self.SUBMIT_BUTTON)
        self.sleep(10) 