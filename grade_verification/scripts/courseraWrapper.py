# external imports
import os
import platform
import csv
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# internal imports
from grade_verification.scripts.getData import (
    get_chrome_user_data_dir,
    get_chrome_profile_dir,
)
from grade_verification.page_objects.home_page import HomePage
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
        self.course_page = CoursePage(self.driver)

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        
        # For headless mode use the provided user data directory and profile;
        # for visible mode, do NOT add these to avoid conflicts.
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
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        # Lower the implicit wait to speed up lookups; explicit waits are used elsewhere.
        driver.implicitly_wait(3)
        
        return driver

    def _perform_visible_login(self):
        """
        Launch a temporary visible driver to allow the user to log in manually.
        Once logged in, extract the session cookies and transfer them to the headless driver.
        """
        print("Launching temporary visible login driver...")
        # Initialize a temporary driver in non-headless mode (without shared user data)
        login_driver = self._init_driver(headless=False)
        login_driver.maximize_window()
        
        # Create temporary page objects for the visible driver
        temp_home_page = HomePage(login_driver)
        
        # Navigate to Coursera in the visible driver
        login_driver.get("https://www.coursera.org")
        # Instead of a fixed sleep, wait up to 5 seconds for a key element (e.g. login button) to appear.
        try:
            WebDriverWait(login_driver, 5, poll_frequency=0.5).until(
                EC.presence_of_element_located(temp_home_page.LOGIN_SELECTOR)
            )
        except Exception:
            pass
        
        # Try auto-triggering login; if it fails, instruct the user.
        try:
            temp_home_page.click_login()
        except Exception as e:
            print("Could not auto-trigger login; please click the login button manually in the visible window.")
        
        # Wait for manual login to complete using an explicit wait (up to 60 seconds, polling every 0.5 sec).
        print("Waiting for manual login completion in the visible window...")
        try:
            WebDriverWait(login_driver, 60, poll_frequency=0.5).until(
                lambda d: temp_home_page.is_logged_in()
            )
        except Exception as e:
            print("Manual login timed out.")
            login_driver.quit()
            raise e
        
        print("Manual login detected in visible window. Extracting cookies...")
        cookies = login_driver.get_cookies()
        login_driver.quit()
        print("Visible login driver closed.")
        
        # Transfer cookies to the headless driver.
        self.driver.get("https://www.coursera.org")
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"Could not add cookie {cookie}: {e}")
        # Refresh headless driver and wait for the profile element.
        self.driver.refresh()
        try:
            WebDriverWait(self.driver, 5, poll_frequency=0.5).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_ICON_IDENTIFIER)
            )
        except Exception:
            pass
        
        # Reinitialize the page objects to reference the updated session.
        self.home_page = HomePage(self.driver)
        self.course_page = CoursePage(self.driver)
        
        print("Cookies transferred to headless driver and page objects updated.")

    def login(self):
        """
        Navigates to the home page in headless mode and checks if the user is logged in.
        If not, launches a temporary visible driver for manual login,
        transfers the session (cookies) to the headless driver, and verifies login.
        """
        self.driver.get("https://www.coursera.org")
        # Instead of sleeping 5 seconds, wait up to 3 seconds for the profile icon.
        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.5).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_ICON_IDENTIFIER)
            )
        except Exception:
            pass
        
        if self.home_page.is_logged_in():
            print("CourseraWrapper.login(): Already logged in")
            return
        
        print("CourseraWrapper.login(): Not logged in in headless mode, launching visible login window...")
        self._perform_visible_login()
        
        self.driver.get("https://www.coursera.org")
        try:
            WebDriverWait(self.driver, 3, poll_frequency=0.5).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_ICON_IDENTIFIER)
            )
        except Exception:
            pass
        
        if self.home_page.is_logged_in():
            print("Login successful on headless driver after cookie transfer.")
        else:
            print("Login still not detected on headless driver!")

    def scrape_courses(self):
        """
        1. Assumes we are on the Coursera home page and already logged in.
        2. Clicks the profile button and then the 'Educator Admin' link.
        3. Waits explicitly for the course list to load.
        4. Scrapes the courses from the dashboard.
        5. Prompts the user to select the sections to scrape.
        """
        # Use the HomePage method to navigate to the Admin dashboard.
        self.home_page.scrape_courses()
        
        # Assume that CoursePage.TABLE_BODY_LOCATOR (e.g., "tbody.css-11pawnl") appears when courses are loaded.
        WebDriverWait(self.driver, 5, poll_frequency=0.5).until(
            EC.visibility_of_element_located(CoursePage.TABLE_BODY_LOCATOR)
        )
        print("scrape_courses(): Navigated to Educator Admin dashboard.")

        # Scrape courses using CoursePage.
        course_list = self.course_page.scrape_courses()

        print("\n--- COURSE / SECTION LIST ---")
        if not course_list:
            print("No courses found.")
            return
        else:
            for i, (course, section) in enumerate(course_list, start=1):
                print(f"{i}. Course: {course} | Section: {section}")
        print("--------------------------------\n")

        # Prompt user for selection.
        choice_input = input("Enter the number of sections to scrape in comma-separated format (e.g. 1,2,3...): ")
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
        self.selected_sections = [course_list[i - 1] for i in selected_indices]
        if not self.selected_sections:
            print("No valid selections made. Exiting scrape_courses().")
            return

        print("\nYou selected the following sections:")
        for (c, s) in self.selected_sections:
            print(f"  Course: {c}, Section: {s}")

        return self.selected_sections

    def group_sessions_by_course(self, selected_sections):
        """
        Given selected_sections as a list of (course, section) tuples,
        returns a dictionary mapping each course to a list of its sections.
        """
        grouped = {}
        for course, section in selected_sections:
            grouped.setdefault(course, []).append(section)
        return grouped

    def scrape_grades_grouped(self, course, session, col_selection):
        """
        For the given course and session, using the user’s column selection (a tuple of 
        (selected_headers, primary_key_full_index)), this function:
         1. Re‑navigates to the Gradebook Manager view (by clicking the Grading tab and then
            the Gradebook Manager link).
         2. Waits until the grade table body is present.
         3. Filters each row for the selected columns (reordering so that the primary key column is first).
         4. Writes the session’s grade data to a CSV file named:
            "Coursera Gradebook - {session} - {course}.csv"
         5. Returns the CSV filepath.
        """
        import csv, re
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from grade_verification.page_objects.session_page import SessionPage

        # Create a new SessionPage object (assumes we are already on the correct session page).
        session_page = SessionPage(self.driver)

        # Wait until the grade table body is present.
        try:
            WebDriverWait(self.driver, 30, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
            print(f"DEBUG: Grade table body not found for session '{session}'.")
            return None

        # Get the grade table rows.
        rows = session_page.get_grade_rows()
        if not rows:
            print(f"No grade rows found for session '{session}'; skipping.")
            return None

        # Get the full column headers.
        full_headers = session_page.get_column_headers()
        print(f"DEBUG: Full header list from table: {full_headers}")

        # Unpack the user's column selection.
        selected_headers, pk_index = col_selection

        # Map the selected headers (from the course selection) to indices in full_headers.
        selected_indices = []
        for sel in selected_headers:
            try:
                idx = full_headers.index(sel)
                selected_indices.append(idx)
            except ValueError:
                print(f"Warning: Selected header '{sel}' not found in full header list for session '{session}'.")
        # Ensure the primary key is the first column.
        if pk_index in selected_indices:
            selected_indices.remove(pk_index)
        selected_indices.insert(0, pk_index)

        # Filter each row for the selected columns.
        data_rows = []
        for row in rows:
            filtered = [row[i] if i < len(row) else "" for i in selected_indices]
            data_rows.append(filtered)

        # Build the output CSV filename.
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        def sanitize_filename(s):
            return re.sub(r'[^a-zA-Z0-9_\-]', '_', s)
        filename = f"Coursera Gradebook - {sanitize_filename(session)} - {sanitize_filename(course)}.csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header_row = [full_headers[i] if i < len(full_headers) else "" for i in selected_indices]
            writer.writerow(header_row)
            for data in data_rows:
                writer.writerow(data)
        print(f"Saved grade data for session '{session}' to {filepath}")

        return filepath


    def scrape_columns_grouped(self, selected_sections):
        """
        For each unique course (group of sessions):
         1. Uses the first session to navigate to the Gradebook Manager view.
         2. Optionally toggles the "Show staff learners" option.
         3. Scrapes the full column headers.
         4. Prompts the user to select which columns to scrape.
         5. Prompts the user to choose the primary key column (from their selection).
         6. Stores the selection for that course.
         7. Then, for each session associated with the course:
              a. Navigates to the session page.
              b. Re‑navigates to the Gradebook Manager view.
              c. Calls scrape_grades_grouped() to scrape the grade table and output a CSV.
         8. Returns a dictionary mapping (course, session) to the CSV filepath.
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from grade_verification.page_objects.session_page import SessionPage

        grouped = self.group_sessions_by_course(selected_sections)
        course_column_selections = {}
        grade_files = {}

        for course, sessions in grouped.items():
            if not sessions:
                continue
            first_session = sessions[0]
            print(f"\nProcessing course '{course}' using session '{first_session}' for column selection.")
            session_link_locator = (By.XPATH, f"//tr//a[normalize-space(text())='{first_session}']")
            try:
                self.course_page.js_click(session_link_locator)
            except Exception as e:
                print(f"Could not click session link for session '{first_session}': {e}")
                continue

            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.visibility_of_element_located(SessionPage.GRADING_TAB_BUTTON)
            )
            session_page = SessionPage(self.driver)
            session_page.go_to_grading_tab()
            self.course_page.sleep(1)
            session_page.open_gradebook_manager()
            self.course_page.sleep(1)

            # Ask if staff users should be shown (applies to all sessions for this course).
            show_staff = input("Would you like to show staff users in the grade table? (y/n): ").strip().lower()                

            # Scrape full column headers.
            headers = session_page.get_column_headers()
            print(f"\n--- COLUMN HEADERS for course '{course}' (from session '{first_session}') ---")
            for idx, header in enumerate(headers, start=1):
                print(f"{idx}. {header}")
            print("--------------------------------------------------------------")

            # Prompt for column selection.
            user_input = input("Enter the numbers of columns to scrape (e.g. 1,3,5): ")
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
            selected_headers = [headers[i-1] for i in selected_column_indices]

            # Prompt for primary key column (from the selected headers).
            while True:
                pk_input = input("Enter the number (from your selection) for the primary key column: ").strip()
                if pk_input.isdigit():
                    pk = int(pk_input)
                    if 1 <= pk <= len(selected_headers):
                        pk_full_index = headers.index(selected_headers[pk-1])
                        break
                    else:
                        print("Input out of range. Please try again.")
                else:
                    print("Invalid input. Please enter a number.")

            course_column_selections[course] = (selected_headers, pk_full_index)
            print(f"\nFinal column selections for course '{course}':")
            print("  Selected columns: ", selected_headers)
            print("  Primary key (full header index): ", pk_full_index)

            # Navigate back to the courses overview page.
            for _ in range(3):
                self.driver.back()
                self.course_page.sleep(1)

            # Now process each session for this course.
            for session in sessions:
                print(f"\nScraping grade table for session '{session}' of course '{course}'...")
                session_link_locator = (By.XPATH, f"//tr//a[normalize-space(text())='{session}']")
                try:
                    self.course_page.expand_all_sections()
                    self.course_page.js_click(session_link_locator)
                except Exception as e:
                    print(f"Could not click session link for session '{session}': {e}")
                    continue

                # Re-navigate to the Gradebook view.
                session_page = SessionPage(self.driver)
                session_page.go_to_grading_tab()
                self.course_page.sleep(1)
                session_page.open_gradebook_manager()
                self.course_page.sleep(1)
                if show_staff == "y":
                    session_page.toggle_staff_learners(show_staff=True)
                    self.course_page.sleep(1)
                # Call scrape_grades_grouped() for this session.
                csv_path = self.scrape_grades_grouped(course, session, course_column_selections[course])
                if csv_path:
                    grade_files[(course, session)] = csv_path

                # Navigate back to the courses overview page.
                for _ in range(3):
                    self.driver.back()
                    self.course_page.sleep(1)
                
            # End processing for this course.
        return grade_files

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
    grade_files = coursera.scrape_columns_grouped(selected_sections)
    # Then, scrape the grade data for each session using those selections.