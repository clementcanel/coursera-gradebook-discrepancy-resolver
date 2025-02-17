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
        # init the driver in headless mode by default
        self.driver = self._init_driver(headless=True)
        # init page objects with the current driver
        self.home_page = HomePage(self.driver)
        self.course_page = CoursePage(self.driver)
        self.base_page = BasePage(self.driver)
        self.session_page = SessionPage(self.driver)
        self.selected_sections = [] # will hold list of (course, session) tuples

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
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
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_ICON_IDENTIFIER)
            )
        except Exception:
            pass
        if self.home_page.is_logged_in():
            print("Already logged in...")
            return
        print("Not logged in... Please manually login...")
        # launch a temporary visible driver for manual login
        visible_driver = self._init_driver(headless=False)
        visible_driver.maximize_window()
        temp_home = HomePage(visible_driver)
        visible_driver.get("https://www.coursera.org")
        try:
            WebDriverWait(visible_driver, 5).until(
                EC.presence_of_element_located(temp_home.LOGIN_SELECTOR)
            )
        except Exception:
            pass
        try:
            temp_home.click_login()
        except Exception as e:
            print("Please log in manually in the visible window.")
        WebDriverWait(visible_driver, 60).until(lambda d: temp_home.is_logged_in())
        cookies = visible_driver.get_cookies()
        visible_driver.quit()
        print("Transferring cookies to headless driver...")
        self.driver.get("https://www.coursera.org")
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"Error adding cookie: {e}")
        self.driver.refresh()
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located(self.home_page.PROFILE_ICON_IDENTIFIER)
        )
        # reinitialize home pagein case cookies changed session state
        self.home_page = HomePage(self.driver)
        print("Login successful on headless driver...")

    def nav_to_admin(self):
        """navigates from the home page to the educator admin dashboard"""

        self.home_page.scrape_courses() # clicks profile and admin link
        WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located(CoursePage.TABLE_BODY_LOCATOR)
        )
        print("Navigated to Educator Admin dashboard...")

    def collect_course_sections(self):
        """scrapes available courses and sections then prompts the user to select sections to scrape"""

        course_list = self.course_page.scrape_courses()
        if not course_list:
            print("No courses found...")
            return []
        print("\n--- COURSE / SECTION LIST ---")
        for i, (course, section) in enumerate(course_list, start=1):
            print(f"{i}. Course: {course} | Section: {section}")
        print("------------------------------")
        choice = input("Enter section numbers to scrape (e.g. 1,3,5): ")
        indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
        selected = [course_list[i - 1] for i in indices if 1 <= i <= len(course_list)]
        print("Selected sections:")
        for c, s in selected:
            print(f"  Course: {c}, Section: {s}")
        self.selected_sections = selected
        return selected

    def group_course_sessions(self, selected_sections):
        """returns a dict mapping each course to its list of sessions"""
        grouped = {}
        for course, session in selected_sections:
            grouped.setdefault(course, []).append(session)
        return grouped

    def collect_course_columns(self, course, sessions):
        """
        - for a given course it uses its first session to navigate to the gradebook manager
        - toggles staff learners, scrapes column headers, and prompts the user to select columns and the primary key
        - returns a tuple: (selected_headers, primary_key_full_index, show_staff)
        """
        print(f"\nProcessing course '{course}' using session '{sessions[0]}' for column selection.")
        session_locator = (By.XPATH, f"//tr//a[normalize-space(text())='{sessions[0]}']")
        try:
            self.course_page.click(session_locator)
        except Exception as e:
            print(f"Could not click session '{sessions[0]}': {e}")
            return None
        WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located(SessionPage.GRADING_TAB_BUTTON)
        )
        self.session_page.go_to_grading_tab()
        self.session_page.open_gradebook_manager()
        show_staff = input("Would you like to process staff users? (y/n): ").strip().lower()
        headers = self.session_page.get_column_headers()
        print(f"\n--- COLUMN HEADERS for course '{course}' (session '{sessions[0]}') ---")
        for idx, header in enumerate(headers, start=1):
            print(f"{idx}. {header}")
        print("----------------------------------------------------")
        col_input = input("Enter numbers of columns to scrape (e.g. 1,3,5): ")
        indices = [int(x.strip()) for x in col_input.split(",") if x.strip().isdigit()]
        selected_headers = [headers[i - 1] for i in indices if 1 <= i <= len(headers)]
        while True:
            pk_input = input("Enter the number of the primary key column to use from your selections (e.g. 1): ").strip()
            if pk_input.isdigit():
                pk = int(pk_input)
                if 1 <= pk <= len(selected_headers):
                    pk_full_index = headers.index(selected_headers[pk - 1])
                    break
                else:
                    print("Input out of range.")
            else:
                print("Invalid input.")
        for _ in range(3):
            self.driver.back()
        return (selected_headers, pk_full_index, show_staff)

    def process_sessions(self, course, col_selection):
        """
        - for a given course and its column configuration it iterates over each session,
        - navigates to its gradebook manager view, scrapes the grade table into a CSV,
        - returns a dict mapping (course, session) to CSV filepath
        """
        grade_files = {}
        for session in self.group_course_sessions(self.selected_sections).get(course, []):
            print(f"\nScraping grade data for session '{session}' of course '{course}'...")
            session_locator = (By.XPATH, f"//tr//a[normalize-space(text())='{session}']")
            try:
                self.course_page.expand_all_sections()
                self.course_page.click(session_locator)
            except Exception as e:
                print(f"Could not click session '{session}': {e}")
                continue
            self.session_page.go_to_grading_tab()
            self.session_page.open_gradebook_manager()
            csv_path = self.scrape_grades(course, session, col_selection)
            if csv_path:
                grade_files[(course, session)] = csv_path
            for _ in range(3):
                self.driver.back()
        return grade_files

    def scrape_grades(self, course, session, col_selection):
        """
        - for the given course and session, using the provided column configuration,
        - waits for the grade table to appear then filters rows for the selected columns
        - writes the data to a CSV file and returns the filepath
        """
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
            print(f"Grade table not found for session '{session}'.")
            return None

        selected_headers, pk_index, toggle_staff = col_selection
        if toggle_staff == "y":
            self.session_page.toggle_staff_learners()
        rows = self.session_page.get_grade_rows()
        if not rows:
            print(f"No grade rows found for session '{session}'; skipping.")
            return None
        full_headers = self.session_page.get_column_headers()
        selected_indices = []
        for sel in selected_headers:
            try:
                idx = full_headers.index(sel)
                selected_indices.append(idx)
            except ValueError:
                print(f"Warning: Header '{sel}' not found for session '{session}'.")
        if pk_index in selected_indices:
            selected_indices.remove(pk_index)
        selected_indices.insert(0, pk_index)
        data_rows = []
        for row in rows:
            filtered = [row[i] if i < len(row) else "" for i in selected_indices]
            data_rows.append(filtered)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)
        output_dir = os.path.join(base_dir, "Coursera-Gradebooks")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"Coursera Gradebook - {BasePage.sanitize_filename(session)} - {BasePage.sanitize_filename(course)}.csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header_row = [full_headers[i] if i < len(full_headers) else "" for i in selected_indices]
            writer.writerow(header_row)
            writer.writerows(data_rows)
        print(f"Saved grade data for session '{session}' to {filepath}")
        return filepath

    def process_courses(self):
        """
        the main workflow method
        - navigates to the admin dashboard, collects course sections,
        - groups them by course and for each course:
          1. configures column selection (and staff toggle) using the first session
          2. processes each session by scraping its grade data into a CSV
        returns a dictionary mapping (course, session) to CSV filepath
        """
        self.nav_to_admin()
        self.collect_course_sections()
        grouped = self.group_course_sessions(self.selected_sections)
        overall_grade_files = {}
        for course, sessions in grouped.items():
            col_selection = self.collect_course_columns(course, sessions)
            if not col_selection:
                continue
            grade_files = self.process_sessions(course, col_selection)
            overall_grade_files.update(grade_files)
        return overall_grade_files


def main():
    controller = CourseraController()
    controller.perform_login()
    grade_files = controller.process_courses()

if __name__ == "__main__":
    main()