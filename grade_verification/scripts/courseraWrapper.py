# external imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# internal imports
from grade_verification.scripts.getData import (
    get_chrome_user_data_dir,
    get_chrome_profile_dir,
    get_coursera_password,
    get_coursera_username
)
from grade_verification.page_objects.home_page import HomePage
from grade_verification.page_objects.login_page import LoginPage

class CourseraWrapper:
    def __init__(self, user_data_dir, profile_dir):
        """
        sets up Chrome with the specified user_data_dir and profile_dir.
        """
        options = webdriver.ChromeOptions()
        if user_data_dir and profile_dir:
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument(f"--profile-directory={profile_dir}")
        else:
            raise Exception("CourseraWrapper.__init__(): missing user data or profile directory")

        # Maximize window
        options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(5)

        # Page objects
        self.home_page = HomePage(self.driver)
        self.login_page = LoginPage(self.driver)

    def login(self, username: str, password: str):
        """
        - navigates to the home page
        - checks if the user is already logged in
        - if not, performs the login steps
        """
        self.driver.get("https://www.coursera.org")
        self.home_page.sleep(3)  # short delay to let page render

        # stop if user is already logged in
        if self.home_page.is_logged_in():
            print("CourseraWrapper.login(): Already logged in")
            return

        print("CourseraWrapper.login(): Not logged in, proceeding to log in")

        # perform login steps
        self.home_page.click_login()
        self.login_page.login(username, password)

        # If login fails, re-prompt
        while not self.home_page.is_logged_in():
            print("Login failed... Please re-enter your credentials:")
            username = get_coursera_username()
            password = get_coursera_password()
            self.login_page.login(username, password)

        print("Login successful!")

if __name__ == "__main__":
    """
    1. figures out the chrome user data folder (stored in .env)
    2. prompts user to select a chrome profile (stored in .env)
    3. prompts for username & password every run (NOT stored in .env)
    4. creates CourseraWrapper
    5. logs into Coursera
    """
    user_data_dir = get_chrome_user_data_dir()
    profile_dir = get_chrome_profile_dir(user_data_dir)

    # prompt for username and password
    username = get_coursera_username()
    password = get_coursera_password()

    coursera = CourseraWrapper(user_data_dir, profile_dir)
    coursera.login(username, password)