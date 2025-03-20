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
        os.system('cls' if os.name == 'nt' else 'clear')
        print("1) Begining setup for CU MS-CS Coursera Grade Scraper...")
        print("--------------------------------------------------------\n")
        # init the driver in headless mode by default
        self.driver = self._init_driver(headless=True)
        # init page objects with the current driver
        self.home_page = HomePage(self.driver)
        self.course_page = CoursePage(self.driver)
        # load base page, and tester mode toggle
        self.base_page = BasePage(self.driver)
        test_selection = input("Are you testing on dummy courses? (enter y/n):")
        if test_selection == "y":
            self.course_list = self.base_page.test_courses
            self.testing = True
        else:
            self.course_list = self.base_page.courses
            self.testing = False

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
            print("   User successfully logged in...")
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
        self.perform_login()
        """
        presents the static list of courses to the user and prompts for selection
        returns a list of selected course titles.
        """
        self.nav_to_admin()
        if not self.testing:
            os.system('cls' if os.name == 'nt' else 'clear')
        print("Successfully navigated to the Educator Admin dashboard...")
        self.admin_dashboard_url = self.driver.current_url
        print("\n--- Available Courses ---")
        for i, course in enumerate(self.course_list, start=1):
            print(f"{i}. {course}")
        print("-------------------------")
        choice = input("Enter course numbers to process (comma-separated): ")
        indices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
        selected = [self.course_list[i - 1] for i in indices if 1 <= i <= len(self.course_list)]
        if not self.testing:
            os.system('cls' if os.name == 'nt' else 'clear')
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

        
        self.driver.get(fs_link)
        self.base_page.sleep(2)
        if not self.testing:
            os.system('cls' if os.name == 'nt' else 'clear')

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
            if pk_input.isdigit() and int(pk_input) in selected_column_indices:
                    # pk in the "selected" sense
                    pk_primary = int(pk_input) - 1
                    break
            else:
                print("Invalid input. Please enter the number assigned to one of your selected columns.")

        while True:
            ppq_input = input("Enter the number of the column that denotes program policy quiz completion: ").strip()
            if ppq_input.isdigit() and int(ppq_input) in selected_column_indices:
                    # pk in the "selected" sense
                    ppq_primary = int(ppq_input) - 1
                    break
            else:
                print("Invalid input. Please enter the number assigned to one of your selected columns.")
        
        # Build the needed tuple: (selected_headers, pk_full_index)
        selected_headers = [headers[i - 1] for i in list(selected_column_indices)]
        pk_full_index = headers.index(selected_headers[pk_primary])
        ppq_full_index = headers.index(selected_headers[ppq_primary])
        col_selection = (selected_headers, pk_full_index, ppq_full_index)

        # Now scrape the first session with these columns
        # Then navigate back to the courses page (or do the next link).
        if not self.testing:
            os.system('cls' if os.name == 'nt' else 'clear')
        self.scrape_grades_for_session(course_title, fs_s, fs_link, col_selection)

        # For subsequent selected links
        for sindex in range(1, len(selected_links)):
            sc_c, sc_s, sc_link = selected_links[sindex]
            self.scrape_grades_for_session(course_title, sc_s, sc_link, col_selection)

        print(f"Finished scraping for course '{course_title}'.")

    def scrape_grades_for_session(self, course_name, session_name, link, col_selection):
        print(f"\nScraping session '{session_name}' at link: {link}")
        self.driver.get(link)

        (selected_headers, pk_full_index, ppq_full_index) = col_selection
        if self.testing:
            self.session_page.toggle_staff_learners()

        # Wait for table to appear
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
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
        if ppq_full_index in selected_indices:
            full_headers[ppq_full_index] = "Policy Quiz"

        # filter each row
        data_rows = []
        for row in rows:
            filtered = [row[i] if i < len(row) else "" for i in selected_indices]
            data_rows.append(filtered)

        # Build header row from selected indices
        header_row = [full_headers[i] if i < len(full_headers) else "" for i in selected_indices]

        # If in testing mode and there is a "Name" column, split it and add Student ID
        if self.testing and "Name" in header_row:
            name_idx = header_row.index("Name")
            # Remove "Name" and insert "First Name" and "Last Name" at its position
            header_row.pop(name_idx)
            header_row.insert(name_idx, "Last Name")
            header_row.insert(name_idx, "First Name")
            # Append Student ID column at the end
            header_row.append("Student ID")

            # Prepare a dictionary to assign unique IDs per unique name
            student_ids = {}
            next_student_id = 100000001

            # Process each data row accordingly
            new_data_rows = []
            for row in data_rows:
                # Extract the original name value from the appropriate column
                original_name = row[name_idx] if name_idx < len(row) else ""
                # Simple split: first token as first name, last token as last name
                if original_name.strip():
                    parts = original_name.strip().split()
                    first_name = parts[0]
                    last_name = parts[-1] if len(parts) > 1 else ""
                else:
                    first_name, last_name = "", ""
                # Remove the original "Name" entry and insert first and last names
                row.pop(name_idx)
                row.insert(name_idx, first_name)
                row.insert(name_idx + 1, last_name)
                # Assign a unique student ID for this name
                if original_name not in student_ids:
                    student_ids[original_name] = next_student_id
                    next_student_id += 1
                row.append(str(student_ids[original_name]))
                new_data_rows.append(row)
            data_rows = new_data_rows

        # Add new column "catalog" from the session_name (assumes session_name.split() returns at least 2 tokens)
        session_title_parts = session_name.split()
        catalog_value = session_title_parts[1] if len(session_title_parts) > 1 else ""
        header_row.append("Catalog No.")
        for row in data_rows:
            row.append(catalog_value)

        # final output path
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        output_dir = os.path.join(base_dir, "Coursera-Gradebooks")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"Coursera_Gradebook_{BasePage.sanitize_filename(session_title_parts[1])}_{BasePage.sanitize_filename(session_title_parts[0])}.csv"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header_row)
            writer.writerows(data_rows)
        if not self.testing:
            os.system('cls' if os.name == 'nt' else 'clear')

        print(f"Saved session '{session_name}' data to {filepath}.")


def main():
    controller = CourseraController()
    controller.main_flow()

if __name__ == "__main__":
    main()