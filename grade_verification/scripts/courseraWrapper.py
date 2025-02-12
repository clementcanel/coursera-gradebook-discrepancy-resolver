# external imports
import os
import platform
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# internal imports
from grade_verification.scripts.getData import (
    get_chrome_user_data_dir,
    get_chrome_profile_dir,
)
from grade_verification.page_objects.home_page import HomePage
from grade_verification.page_objects.login_page import LoginPage
from grade_verification.page_objects.course_page import CoursePage
from grade_verification.page_objects.session_page import SessionPage

class CourseraWrapper:
    def __init__(self, user_data_dir, profile_dir):
        """
        - sets up Chrome with the given user_data_dir and profile_dir
        - inits the main Selenium driver in headless mode
        """
        # save these for later use (i.e. when reinitializing the driver)
        self.user_data_dir = user_data_dir
        self.profile_dir = profile_dir

        # initialize the driver in headless mode by default
        self.driver = self._init_driver(headless=True)
        
        # initialize page objects with the current driver
        self.home_page = HomePage(self.driver)
        self.login_page = LoginPage(self.driver)
        self.course_page = CoursePage(self.driver)

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        
        # for headless mode use the provided user data directory and profile
        # for visible mode do NOT add these to avoid conflicts
        if headless:
            if self.user_data_dir and self.profile_dir:
                options.add_argument(f"--user-data-dir={self.user_data_dir}")
                options.add_argument(f"--profile-directory={self.profile_dir}")
            else:
                raise Exception("CourseraWrapper.__init__(): missing user data or profile directory")
        
        options.add_argument("--start-maximized")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        if headless:
            options.add_argument("--headless=new")
            # full-screen for headless mode:
            options.add_argument("--window-size=1920,1080")
        else:
            # For visible mode also use a large window size
            options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)
        
        return driver

    def _perform_visible_login(self):
        """
        launch a temporary visible driver to allow the user to log in manually
        once logged in, extract the session cookies and transfer them to the headless driver
        """
        print("Launching temporary visible login driver...")
        # initialize a temporary driver in non-headless mode (without using the shared user data)
        login_driver = self._init_driver(headless=False)
        
        # maximize the visible window so the user can interact with it
        login_driver.maximize_window()
        
        # create temporary page objects for the visible driver
        temp_home_page = HomePage(login_driver)
        temp_login_page = LoginPage(login_driver)
        
        # navigate to Coursera in the visible driver
        login_driver.get("https://www.coursera.org")
        temp_home_page.sleep(5)  # Wait for the page to render

        # try to click the login button if available in visible mode
        try:
            temp_home_page.click_login()
        except Exception as e:
            print("Could not auto-trigger login; please click the login button manually in the visible window.")
        
        # wait for manual login completion
        print("Waiting for manual login completion in the visible window...")
        while not temp_home_page.is_logged_in():
            temp_home_page.sleep(2)
        
        print("Manual login detected in visible window. Extracting cookies...")
        # extract cookies from the visible (login) driver
        cookies = login_driver.get_cookies()
        
        # elose the visible login driver
        login_driver.quit()
        print("Visible login driver closed.")
        
        # update the headless driver with the cookies
        self.driver.get("https://www.coursera.org")
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"Could not add cookie {cookie}: {e}")
        
        # refresh the headless driver to apply the cookies
        self.driver.refresh()
        self.home_page.sleep(5)
        
        # reinitialize the page objects to ensure they reference the updated session
        self.home_page = HomePage(self.driver)
        self.login_page = LoginPage(self.driver)
        self.course_page = CoursePage(self.driver)
        
        print("Cookies transferred to headless driver and page objects updated.")

    def login(self):
        """
        navs to the home page in headless mode and checks if the user is logged in
        if not it launches a temporary visible driver for manual login and
        transfers the session (cookies) to the headless driver, and verifies login
        """
        # nav to the home page in the headless driver
        self.driver.get("https://www.coursera.org")
        self.home_page.sleep(5)  # Allow time for full rendering
        
        # if already logged in return immediately
        if self.home_page.is_logged_in():
            print("CourseraWrapper.login(): Already logged in")
            return

        # otherwise continue with visible login
        print("CourseraWrapper.login(): Not logged in in headless mode, launching visible login window...")
        self._perform_visible_login()

        # at this point the headless driver should have the session cookies
        # confirm login on headless instance
        self.driver.get("https://www.coursera.org")  # refresh to apply cookies
        self.home_page.sleep(5)
        if self.home_page.is_logged_in():
            print("Login successful on headless driver after cookie transfer.")
        else:
            print("Login still not detected on headless driver!")

    def scrape_courses(self):
        """
        1. assumes we are on the Coursera home page and already logged in
        2. clicks the profile button in the header
        3. clicks the 'Educator Admin' link to go to /admin/
        """
        self.home_page.scrape_courses()
        self.home_page.sleep(2)
        print("scrape_courses(): Navigated to Educator Admin dashboard.")

        # scrape courses
        course_list = self.course_page.scrape_courses()

        # print them with numeric indices
        print("\n--- COURSE / SECTION LIST ---")
        if not course_list:
            print("No courses found.")
            return  # nothing more to do
        else:
            for i, (course, section) in enumerate(course_list, start=1):
                print(f"{i}. Course: {course} | Section: {section}")
        print("--------------------------------\n")

        # prompt user for selection
        choice_input = input(
            "Enter the number of sections to scrape in comma-separated format (e.g. 1,2,3...): "
        )

        # parse the users input
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

        # build a list of the user-selected (course, section) pairs
        self.selected_sections = [course_list[i - 1] for i in selected_indices]

        if not self.selected_sections:
            print("No valid selections made. Exiting scrape_courses().")
            return

        # print the selected sections
        print("\nYou selected the following sections:")
        for (c, s) in self.selected_sections:
            print(f"  Course: {c}, Section: {s}")

        return self.selected_sections

    def scrape_columns(self, selected_sections):
        """
        for each selected course/session it:
         1. clicks on the session link corresponding to the selected section
         2. on the session page itclicks the 'Grading' tab
         3. in the 'Grading' view it clicks the 'Gradebook Manager' link
         4. scrapes the column headers from the grade table
         5. prompts the user to select which columns to scrape
         6. returns a dictionary mapping (course, section) to the list of selected column headers
        """
        results = {}
        for course, section in selected_sections:
            # click the session link for this section
            # we assume that the link text exactly matches the section name
            session_link_locator = (By.XPATH, f"//tr//a[normalize-space(text())='{section}']")
            try:
                self.course_page.js_click(session_link_locator)
            except Exception as e:
                print(f"Could not click session link for section '{section}': {e}")
                continue
            
            # wait for the session page to load
            self.course_page.sleep(5)
            
            # init the SessionPage page object
            session_page = SessionPage(self.driver)
            
            # click on the Grading tab
            session_page.go_to_grading_tab()
            
            # click the Gradebook Manager link in the sidebar
            session_page.open_gradebook_manager()
            
            # wait for the gradebook view to load
            session_page.sleep(5)
            
            # scrape the column headers from the grade table
            headers = session_page.get_column_headers()
            print(f"\n--- COLUMN HEADERS FOR SECTION: {section} ---")
            for idx, header in enumerate(headers, start=1):
                print(f"{idx}. {header}")
            print("--------------------------------")
            
            # prompt the user to pick which columns to scrape
            user_input = input("Enter the numbers of columns to scrape in comma-separated format (e.g. 1,3,5): ")
            selected_column_indices = []
            for token in user_input.split(","):
                token = token.strip()
                if token.isdigit():
                    idx = int(token)
                    if 1 <= idx <= len(headers):
                        selected_column_indices.append(idx)
                    else:
                        print(f"Index {idx} is out of range.")
                else:
                    print(f"Invalid input: {token}")
            
            # save the selected header names
            selected_headers = [headers[i-1] for i in selected_column_indices]
            results[(course, section)] = selected_headers
            
            # navigate back to the courses page so the next session can be processed
            self.course_page.sleep(3)
        
        print("\nFinal selected column headers for each section:")
        for key, value in results.items():
            print(f"Section {key}: {value}")

        return results
    
    def scrape_grades(self, column_selections):
        """
        given the dictionary 'column_selections' (mapping (course, section) to a list of selected column headers)
        this function:
         1. prompts the user to select a primary key column for each session
         2. scrapes the grade table rows from the gradebook view
         3. stores the selected columns (with the primary key column as the first column)
            in a CSV file in an 'output' folder adjacent to this file
         4. returns a dictionary mapping (course, section) to the filepath of the CSV file
        """
        primary_keys = {}  # mapping from (course, section) to primary key index (0 indexed)
        for key, headers in column_selections.items():
            course, section = key
            print(f"\nFor section {section} of course {course}, the selected columns are:")
            for idx, header in enumerate(headers, start=1):
                print(f"{idx}. {header}")
            while True:
                user_input = input("Enter the number of the column to use as the primary key: ").strip()
                if user_input.isdigit():
                    num = int(user_input)
                    if 1 <= num <= len(headers):
                        primary_keys[key] = num - 1  # store as 0 indexed
                        break
                    else:
                        print("Input out of range. Please try again.")
                else:
                    print("Invalid input. Please enter a number.")
        
        results = {}
        for key, headers in column_selections.items():
            course, section = key
            print(f"\nScraping grade table for section {section} of course {course}...")
            session_page = SessionPage(self.driver)
            rows = session_page.get_grade_rows()
            if not rows:
                print("No grade rows found; skipping this session.")
                continue
        
        return results

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
    selected_sections = coursera.scrape_courses()
    # Now scrape columns (grade table headers) from the selected sections:
    column_selections = coursera.scrape_columns(selected_sections)
    # Finally, scrape the grade data into CSV files:
    grade_files = coursera.scrape_grades(column_selections)