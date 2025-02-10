# external imports
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# internal imports
from grade_verification.scripts.getData import (
    get_chrome_user_data_dir,
    get_chrome_profile_dir,
)
from grade_verification.page_objects.home_page import HomePage
from grade_verification.page_objects.login_page import LoginPage
from grade_verification.page_objects.course_page import CoursePage

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

        options.add_argument("--start-maximized")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        system = platform.system()
        if system == "Windows":
            # Move the window off-screen
            options.add_argument("--window-position=-32000,0")
            options.add_argument("--window-size=800,600")
        else:
            # On macOS/Linux, we'll just minimize after creation
            options.add_argument("--window-size=800,600")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(5)

        if system != "Windows":
            self.driver.minimize_window()
            

        # Page objects
        self.home_page = HomePage(self.driver)
        self.login_page = LoginPage(self.driver)
        self.course_page = CoursePage(self.driver)

    def show_browser(self):
        """
        move or un-minimize the browser window so the user can see it.
        on Windows reset to a normal visible position. On macOS/Linux, restore/maximize.
        """
        system = platform.system()
        if system == "Windows":
            self.driver.set_window_position(100, 100)
            self.driver.set_window_size(1200, 800)
        else:
            self.driver.maximize_window()

    def hide_browser(self):
        """
        hide the browser again by moving it off-screen (Windows) or minimizing (macOS/Linux).
        """
        system = platform.system()
        if system == "Windows":
            self.driver.set_window_position(-32000, 0)
            self.driver.set_window_size(800, 600)
        else:
            self.driver.minimize_window()

    def login(self):
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
        self.home_page.click_login()
        self.show_browser()
        # Keep checking until user is logged in
        while not self.home_page.is_logged_in():
            self.home_page.sleep(2)  # check every 2 seconds

        print("Login successful! Hiding window and quitting.")
        self.hide_browser()

    def nav_to_courses(self):
        """
        1. assumes we are on the Coursera home page and already logged in.
        2. clicks the profile button (user avatar) in the header.
        3. clicks the 'Educator Admin' link to go to /admin/.
        """
        self.home_page.nav_to_courses()
        self.home_page.sleep(2)
        print("nav_to_courses(): Navigated to Educator Admin dashboard.")

        # 1) Scrape courses
        course_list = self.course_page.scrape_courses()

        # 2) Print them with numeric indices
        print("\n--- COURSE / SECTION LIST ---")
        if not course_list:
            print("No courses found.")
            return  # nothing more to do
        else:
            for i, (course, section) in enumerate(course_list, start=1):
                print(f"{i}. Course: {course} | Section: {section}")
        print("--------------------------------\n")

        # 3) Prompt user for selection
        choice_input = input(
            "Enter the number of sections to scrape in comma-separated format (e.g. 1,2,3...): "
        )

        # 4) Parse the user's input
        #    We'll handle invalid inputs by ignoring them or you can raise an error.
        selected_indices = []
        for chunk in choice_input.split(","):
            chunk = chunk.strip()
            if not chunk.isdigit():
                print(f"Skipping invalid input: {chunk}")
                continue
            idx = int(chunk)
            if idx < 1 or idx > len(course_list):
                print(f"Skipping out-of-range selection: {idx}")
                continue
            selected_indices.append(idx)

        # 5) Build a list of the user-selected (course, section) pairs
        self.selected_sections = [course_list[i - 1] for i in selected_indices]

        if not self.selected_sections:
            print("No valid selections made. Exiting nav_to_courses().")
            return

        # 6) Print the selected sections
        print("\nYou selected the following sections:")
        for (c, s) in self.selected_sections:
            print(f"  Course: {c}, Section: {s}")

        return self.selected_sections

    def scrape_grades(self, selected_sections):
        pass

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

    coursera = CourseraWrapper(user_data_dir, profile_dir)
    coursera.login()
    selected_sections = coursera.nav_to_courses()