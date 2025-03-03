# External imports
import os, csv, sys, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Internal imports
from grade_verification.page_objects.home_page import HomePage
from grade_verification.page_objects.course_page import CoursePage
from grade_verification.page_objects.session_page import SessionPage
from grade_verification.page_objects.base_page import BasePage


class CourseraController:
    """
    this controller orchestrates the full grade scraping workflow:
      1. logging in (via a temporary visible login)
      2. navigating to the educator admin dashboard
      3. collecting available course sections (sessions)
      4. for each unique course:
           - configuring column selection (and optionally toggling staff learners) using the first session
           - processing each session to scrape grade data and output a CSV file
    """
    def __init__(self):
        print("1) Begining setup for CU MS-CS Coursera Grade Scraper...")
        print("--------------------------------------------------------\n")
        # init the driver in headless mode by default
        self.driver = self._init_driver(headless=True)
        # init page objects with the current driver
        self.home_page = HomePage(self.driver)
        self.course_page = CoursePage(self.driver)
        self.base_page = BasePage(self.driver)
        self.session_page = SessionPage(self.driver)
        self.selected_sections = [] # will hold list of (course, session, session_url) tuples
        self.admin_dashboard_url = None

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--log-level=1")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(1)
        return driver

    def perform_login(self):
        """logs into Coursera, if already logged in, does nothing"""

        self.driver.get("https://www.coursera.org")
        try:
            WebDriverWait(self.driver, 5).until(lambda d: self.home_page.is_logged_in())
            print("2) Already logged in...")
            return
        except Exception:
            print("2) Not logged in, please login manually...")
            pass

        # launch a temporary visible driver for manual login
        visible_driver = self._init_driver(headless=False)
        visible_driver.maximize_window()
        temp_home = HomePage(visible_driver)

        # nav to home page with visible driver, click login button
        visible_driver.get("https://www.coursera.org")
        try:
            WebDriverWait(visible_driver, 5).until(
                EC.presence_of_element_located(temp_home.LOGIN_SELECTOR)
            )
        except Exception:
            print("Login page failed to load. Retrying...")
            visible_driver.get("https://www.coursera.org")
        try:
            temp_home.click_login()
        except Exception as e:
            print("ERROR: Could not click login button...")
        
        # wait for user to enter login credentials
        print("3) Chrome login window opened. You have 2 minutes to log in...")
        try:
            WebDriverWait(visible_driver, 120).until(lambda d: temp_home.is_logged_in())
            print("User successfully logged in...")
        except Exception as e:
            print("ERROR: No login was detected on visible driver...")
            return

        # retrieve cookies and add them to headless driver
        print("4) Retrieving login cookies...")
        cookies = visible_driver.get_cookies()
        visible_driver.quit()

        print("5) Transferring cookies to headless driver...")
        self.driver.get("https://www.coursera.org")
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"ERROR: problem adding cookie: {e}")
        self.driver.refresh()
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_BUTTON_SELECTOR)
            )
            # reinitialize home pagein case cookies changed session state
            self.home_page = HomePage(self.driver)
            print("6) Login successful on headless driver...")
        except Exception as e:
            print(f"ERROR: Could not transfer login to headless driver: {e}")

    def nav_to_admin(self):
        """navigates from the home page to the educator admin dashboard"""
        print("7) Navigating to Educator Admin dashboard...")
        try:
            self.home_page.scrape_courses() # clicks profile and admin link
        except:
            print("ERROR: Failed to navigate to Educator Admin dashboard...")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(CoursePage.TABLE_BODY_LOCATOR)
            )
        except:
            print("ERROR: Failed to locate Course Section table...")
    
    def main_flow(self):
        """
        presents the static list of courses to the user and prompts for selection
        returns a list of selected course titles.
        """
        self.nav_to_admin()
        print("Successfully navigated to the Educator Admin dashboard...")
        self.admin_dashboard_url = self.driver.current_url
        print("\n--- Available Courses ---")
        for i, course in enumerate(self.base_page.test_courses, start=1):
            print(f"{i}. {course}")
        print("-------------------------")
        choice = input("Enter course numbers to process (comma-separated): ")
        indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
        selected = [self.base_page.test_courses[i - 1] for i in indices if 1 <= i <= len(self.base_page.test_courses)]
        print("Selected courses:")
        for course in selected:
            print(f"  {course}")

        for course_title in selected:
            self.process_single_course(course_title)

    def process_single_course(self, course_title: str):
        if self.driver.current_url != self.admin_dashboard_url:
            self.driver.get(self.admin_dashboard_url)
        # 1) search for the given course title in the search bar
        self.course_page.search_courses(course_title)

        # 2) scrape course sessions from the list of courses that are both 'Live' and prefixed with 'prefix'
        filtered_sessions = self.course_page.scrape_courses(prefix="CSCA") # list of tuples: (course_name, section_name, section_link)

        # 3) prompt user to pick sessions to scrape
        if not filtered_sessions:
            print(f"No sessions were found for '{course_title}' that are both Live and prefixed with 'CSCA'...")
            return
        
        print(f"\n--- Sessions for course '{course_title}' that are 'Live' + start with 'CSCA' ---")
        for i, (c_name, s_name, s_link) in enumerate(filtered_sessions, start=1):
            print(f"{i}. Session: {s_name} | link: {s_link}")
        print("--------------------------------------------------------------")

        choice_input = input("Enter numbers of sessions to scrape (e.g. 1,2,3): ")
        selected_links = []

        for idx_str in choice_input:
            idx = int(idx_str)
            if 1 <= idx <= len(filtered_sessions):
                selected_links.append(filtered_sessions[idx - 1])

        if not selected_links:
            print(f"No sessions selected for '{course_title}'!")
            return

        # 4) for the first link in selected_links, select columns for that session
        print(f"\nNavigating to first session link for course '{course_title}' to configure column selection...")
        # (c_name, s_name, s_link)
        first_session = selected_links[0]
        fs_c, fs_s, fs_link = first_session

        try:
            self.driver.get(fs_link)
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(SessionPage.GRADING_TAB_BUTTON)
            )
        except:
            print("Could not find to the sessions grading tab...")
        
        self.session_page.go_to_grading_tab()
        self.session_page.open_gradebook_manager()
        show_staff = input("Would you like to show staff users in the grade table? (y/n): ").strip().lower()

        headers = self.session_page.get_column_headers()
        print(f"\n--- COLUMN HEADERS for course '{course_title}' (session '{fs_s}') ---")
        for idx, header in enumerate(headers, start=1):
            print(f"{idx}. {header}")
        print("--------------------------------------------------------------")

        user_input = input("Enter the numbers of columns to scrape (e.g. 1,3,5): ")
        selected_column_indices = []
        for token in user_input.split(","):
            token = token.strip()
            if token.isdigit():
                idx = int(token)
                if 1 <= idx <= len(headers):
                    selected_column_indices.append(idx)
                else:
                    print(f"Index {idx} out of range.")
            else:
                print(f"Invalid input: {token}")
        
        while True:
            pk_input = input("Enter the number of the column to use as the primary key: ").strip()
            if pk_input.isdigit():
                pk = int(pk_input)
                if 1 <= pk <= len(selected_column_indices):
                    # pk in the "selected" sense
                    pk_idx_in_selected = pk - 1
                    break
                else:
                    print("Input out of range. Try again.")
            else:
                print("Invalid input. Enter a digit.")
        
        # Build the needed tuple: (selected_headers, pk_full_index, show_staff)
        selected_headers = [headers[i - 1] for i in selected_column_indices]
        pk_full_index = headers.index(selected_headers[pk_idx_in_selected])
        col_selection = (selected_headers, pk_full_index, show_staff)

        # Now scrape the first session with these columns
        # Then navigate back to the courses page (or do the next link).
        self.scrape_grades_for_session(course_title, fs_s, fs_link, col_selection)

        # For subsequent selected links
        for sindex in range(1, len(selected_links)):
            sc_c, sc_s, sc_link = selected_links[sindex]
            self.scrape_grades_for_session(course_title, sc_s, sc_link, col_selection)

        print(f"Finished scraping for course '{course_title}'.")

    def scrape_grades_for_session(self, course_name, session_name, link, col_selection):
        print(f"\nScraping session '{session_name}' at link: {link}")
        self.driver.get(link)

        try:
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located(self.session_page.GRADING_TAB_BUTTON)
            )
            self.session_page.go_to_grading_tab()
            self.session_page.open_gradebook_manager()
        except:
            print(f"failed to navigate to gradebook for course '{course_name}', and session '{session_name}'...")

        (selected_headers, pk_full_index, toggle_staff) = col_selection
        if toggle_staff == "y":
            self.session_page.toggle_staff_learners()

        # Wait for table to appear
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except:
            print(f"Could not locate table body for session '{session_name}'; skipping.")
            return

        # get rows
        rows = self.session_page.get_grade_rows()
        if not rows:
            print(f"No grade rows found for session '{session_name}'; skipping.")
            return

        # get full headers
        full_headers = self.session_page.get_column_headers()

        # map user-chosen 'selected_headers' to indices in full_headers
        selected_indices = []
        for sh in selected_headers:
            try:
                idx = full_headers.index(sh)
                selected_indices.append(idx)
            except ValueError:
                print(f"Warning: Header '{sh}' not found in session '{session_name}' table.")
        if pk_full_index in selected_indices:
            selected_indices.remove(pk_full_index)
        selected_indices.insert(0, pk_full_index)

        # filter each row
        data_rows = []
        for row in rows:
            filtered = [row[i] if i < len(row) else "" for i in selected_indices]
            data_rows.append(filtered)

        # final output path
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        output_dir = os.path.join(base_dir, "Coursera-Gradebooks")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"Coursera Gradebook - {BasePage.sanitize_filename(session_name)} - {BasePage.sanitize_filename(course_name)}.csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header_row = [full_headers[i] if i < len(full_headers) else "" for i in selected_indices]
            writer.writerow(header_row)
            writer.writerows(data_rows)

        print(f"Saved session '{session_name}' data to {filepath}.")

def main():
    controller = CourseraController()
    controller.perform_login()
    controller.main_flow()

if __name__ == "__main__":
    main()