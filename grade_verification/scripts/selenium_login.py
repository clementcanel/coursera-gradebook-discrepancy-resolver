# selenium environment setup tutorial: https://www.youtube.com/watch?v=l-DFyStar9A
# setup:
# - create a new chrome profile
# - find where the profile is stored on your machine
#   - "/Users/<username>/Library/Application Support/Google/Chrome" on mac
#   - you will see a file called something like 'profile 2'
# - update the path to your chrome executable in get_new_driver
# - Update user_data_dir and profile_dir to your files
# - replace the login details with your own
# run program with 'pytest selenium_login.py'

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


class HomeTest:

    # setup chromedriver with user profile
    def get_new_driver(self, *args, **kwargs):
        # file path to local chrome data
        user_data_dir = "/Users/<username>/Library/Application Support/Google/Chrome"
        profile_dir = "<chosen profile>"  # replace with your chrome profile folder name

        # used to configure browser settings
        chrome_options = webdriver.ChromeOptions()
        # specifies where chrome will look for user data
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        # specifies the profile to be used
        chrome_options.add_argument(f"--profile-directory={profile_dir}")
        # the path to your chrome executable (this is the default location on mac)
        chrome_options.binary_location = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        #
        chrome_options.add_argument("--remote-debugging-port=9222")

        # set up chrome driver service with the specified options above
        service = Service(log_path="chromedriver.log")
        return webdriver.Chrome(service=service, options=chrome_options)

    def test_home_page(self):
        # open the home page
        self.open("https://www.coursera.org")

        # selector for the profile dropdown button (only present when logged in)
        profile_dropdown_selector = "button#right-nav-dropdown-btn"

        # check if already logged in using the profile dropdown button
        if self.is_element_visible(profile_dropdown_selector):
            print("Already logged in, test successful")
            return  # Exit the test as no login is needed
        else:
            print("Not logged in, proceeding to log in")

        # if not logged in then perform login steps
        login_button_selector = "a[data-e2e='header-login-button']"
        self.click(login_button_selector)
        username_selector = "input[name='email']"
        self.type(username_selector, "<Coursera Login Email>")
        password_selector = "input[name='password']"
        self.type(password_selector, "<Coursera Login Password>")
        login_form_submit_button = "button[data-e2e='login-form-submit-button']"
        self.click(login_form_submit_button)
        self.sleep(10)

        # verify if login was successful
        if self.is_element_visible(profile_dropdown_selector):
            print("Login successful, test passed")
        else:
            print("Login failed, test failed")
            raise Exception("Login failed")
