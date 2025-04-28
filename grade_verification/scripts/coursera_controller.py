# External imports
import os, csv, sys, ctypes, time, glob
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
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
from grade_verification.page_objects.spinner import Spinner

class CourseraController:

    """
    Function: __init__()
    Purpose: Initializes the CourseraController object, which is responsible for controlling
             Selenium for grade scraping
    Flow:
        1. Initializes chrome driver using the _init_driver() function.
        2. Initializes page objects:
            - base_page: Selenium helper functions
            - home_page: Functions for login including is_logged_in and click_login
            - course_page: Functions for getting session info including search_courses and 
                           scrape_courses
            - session_page: Functions for Gradebook scraping including toggle_staff_learners, 
                            get_column_headers, and get_grade_rows
        3. Verifies the existance of a valid Registrar Record file.
        4. Asks the user if they want to run in test more or not, then sets settings accordingly.
    """
    def __init__(self):
        print("\n")
        spinner = Spinner("      🔄 Booting...")
        spinner.start()
        try:
            # init the driver in headless mode by default
            self.driver = self._init_driver(headless=True)

            # init page objects with the current driver
            self.base_page = BasePage(self.driver)
            self.home_page = HomePage(self.driver)
            self.course_page = CoursePage(self.driver)
            self.session_page = SessionPage(self.driver)
        except:
            print(" Error: Failed to initialize a chrome driver!")
        spinner.stop()
        
        print("\n\n -------------------------------------------------------------------------")
        print(" ----  ✨" + "\033[1m" + " Starting Up The CU MS-CS Coursera Gradebook Validator!" + "\033[0m" + "  ✨  ----")
        print(" -------------------------------------------------------------------------")

        try:
            # Determine the base directory:
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running in a normal Python environment
                base_dir = os.getcwd()
        except Exception as e:
            # Failed to find base directory:
            print(f" Error: Failed to locate the directory that this excutable is running from:\n {e}")
        
        try:
            registrar_files = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
            registrar_file =  max(registrar_files, key=os.path.getmtime)
        except Exception as e:
            print(f" Error: Failed to locate a valid registrar file in your base directory: \n {e}")
            registrar_file = ""

        try:
            if not registrar_file:
                print("\n   ⚠️" + "\033[1m" + " Oh No!" + "\033[0m" + " We couldnt find a valid Registrar Record in the current directory:")
                time.sleep(0.05)
                print(f"      📌" + "\033[1m" + " Current Directory:" + "\033[0m" + f" {base_dir}")
                time.sleep(0.05)
                print(f"      ✅ Ensure that your Registrar Record meets the following specifications:")
                time.sleep(0.05)
                print(f"         ✨ Is placed in the Current Directory, Where you launched this program.")
                time.sleep(0.05)
                print(f"         ✨ Is an Excel '.xslx' file type.")
                time.sleep(0.05)
                print(f"         ✨ Is prefixed with 'GradeAddReport'.")
                time.sleep(0.05)
                print(f"         ✨ Is the most recently added/only 'GradeAddReport' prefixed file.")
                time.sleep(1)
        except Exception as e:
            print(f" Error: Failed to print Registrar File Re-Check Instructions: {e}")

        try:
            while not registrar_file:
                re_check = input("\n   🟢 Please press the return/enter key to re-check for a valid Registrar Record:  ")
                registrar_file = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
                if not registrar_file:
                    print("\n   ⚠️ Failed to find the Registrar Record again...")
                time.sleep(1)
        except Exception as e: 
            print(f" Error: Failed to prompt the user to recheck for Registrar File existance: {e}")

        try:
            registrar_parts = registrar_file.split("\\")
        except Exception as e:
            print(f"Failed to split the registrar file path into parts:\n {e}")

        try: 
            time.sleep(1)
            test_selection = input("\n   🟢 " + "\033[1m" + "Are you running in 'Test' mode? (y/n): " + "\033[0m")
            while test_selection != "y" and test_selection != "Y" and test_selection != "n" and test_selection != 'N':
                test_selection = input("   🟡 Invalid Input: please enter 'y' or 'n': ")
            test_mode_text = "Production Mode"
            if test_selection == "y" or test_selection == 'Y':
                test_mode_text = "Test Mode"

            confirm_test = input(f"   🟢 Press enter/return to confirm your selection of '{test_mode_text}',\n   🟡 or input your new choice: ")
            while confirm_test != "y" and confirm_test != "Y" and confirm_test != "n" and confirm_test != 'N' and confirm_test != "":
                confirm_test = input("   🟡 Invalid Input: please enter'y','n', or leave blank: ")
                if confirm_test == "y" or confirm_test == "Y" and confirm_test == "n" and confirm_test == 'N':
                    test_selection = confirm_test
        except Exception as e:
            print(f" Error: Failed to prompt the user if they would like to run the program in Test or Production mode: {e}")

        try:
            if test_selection == "y":
                self.course_list = self.base_page.test_courses
                self.testing = True
                while True:
                    # log mode will prevent console clears for debuging purposes.
                    cinamode_input = input("\n   🟢 Run in Log Mode? (y/n): ")
                    if cinamode_input == "y" or cinamode_input == "Y":
                        self.cinamode = False
                        break
                    elif cinamode_input == "n" or cinamode_input == "N":
                        self.cinamode = True
                        break
                    else:
                        print("   🟡 Invalid Input: enter either 'y' or 'n' (non case-sensitive)")
                cinamode_text = "Cinimatic" if self.cinamode == True else "Log"
                print("\n      ✅" + "\033[1m" + " Now running in test mode!" + "\033[0m")
                time.sleep(0.05)
                print("         📌 Uses dummy courses defined in the 'test_courses' list.")
                time.sleep(0.05)
                print("         📌 Generates dummy 'Student Id' for each user.")
                time.sleep(0.05)
                print(f"         📌 Running in {cinamode_text} Mode:")
                time.sleep(0.05)
                if self.cinamode:
                    print("            ✨ Program will have a slide-show like flow.")
                else:
                    print("            ✨ Program will never clear the console.")

                time.sleep(0.05)
                print("         📌 Uses Test Registrar Record:")
                registrar_parts = registrar_file.split("\\")
                time.sleep(0.05)
                print(f"            ✨ Record Name: {registrar_parts[-1]}")
                time.sleep(0.05)
                print(f"            ✨ Record Path: {registrar_file[0:(len(registrar_file) - len(registrar_parts[-1]))]}")
                time.sleep(1)
            else:
                self.course_list = self.base_page.courses
                self.testing = False
                self.cinamode = True
                print("\n      ✅" + "\033[1m" + " Now running in Production Mode!" + "\033[0m")
                time.sleep(0.05)
                print("         📌 Promps seleciton of predefined 'CSCA' courses that can be scraped.")
                time.sleep(0.05)
                print("         📌 Uses Registrar Record:")
                time.sleep(0.05)
                print(f"            ✨ Record Name: {registrar_parts[-1]}")
                time.sleep(0.05)
                print(f"            ✨ Record Path: {registrar_parts[0:len(registrar_parts) - len(registrar_parts[-1]) + 1]}")
                time.sleep(0.05)
                print("            ✨ Uses use the most recently accessed .xslx file prefixed with 'GradeAddReport'.")
                time.sleep(0.05)
                print("\n         📌 Auto Selected Gradebook Columns:")
                time.sleep(0.05)
                print("            ✨ Student Id (Primary Key)")
                time.sleep(0.05)
                print("            ✨ Current Grade")
                time.sleep(0.05)
                print("            ✨ First Name")
                time.sleep(0.05)
                print("            ✨ Last Name")
                time.sleep(0.05)
                print("\n         📌 Manually Selected Columns (Variably named across courses):")
                time.sleep(0.05)
                print("            ✨ Honor Code Quiz")
                time.sleep(1)
        except Exception as e:
            print(f" Error: Failed to present details of Mode Selection: {e}")

        try:
            self.selected_sections = [] # will hold list of (course, session, session_url) tuples
            self.admin_dashboard_url = "https://www.coursera.org/admin-v2/boulder/home/courses"
        except Exception as e:
            print(f" Error: Failed to set selected sessions and admin dashboard URL: {e}")
        move_on_input = input("\n   🟢 Press Enter/Return to begin Sign In: ")
        if self.cinamode:
            os.system('cls' if os.name == 'nt' else 'clear')

    """
    Function: _init_driver(headless: bool)
    Purpose: Initializes a chrome driver instance to be used by Selenium for web scraping.
    Flow:
        1. Initializes the following options for the driver to be initialized::
            - --start-maximized: The window starts in its maximized state (widest and tallest window possible)
            - --disable-backgrounding-occluded-windows: always treats the chrome window as visible.
            - --disable-renderer-backgrounding: Keeps DOM rendering of invisible pages fast.
            - --excludeSwitches, enable-logging: Removes some random windows warnings.
            - --log-level=3: ensures only the most dire of errors are displayed to the user.
            - --headless=new/--window-size=1920,1080: makes the window invisible, sets window dimensions again just in case.
        2. Creates a new chrome driver window with the specified settings loaded in.
    """
    def _init_driver(self, headless: bool) -> webdriver.Chrome:

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("--log-level=3")

            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--window-size=1920,1080")
            else:
                options.add_argument("--window-size=1920,1080")
        except Exception as e:
            print(f" Error: Failed to set options for new Chrome Driver Instance: {e}")

        try:
            service = Service(ChromeDriverManager().install(), log_path=os.devnull)
            driver = webdriver.Chrome(service=service, options=options)
            os.system('cls' if os.name == 'nt' else 'clear')
            driver.implicitly_wait(1)
        except Exception as e:
            print(f" ERROR: Failed to launch chrome driver: {e}")

        return driver


    """
    Function: perform_login()
    Purpose: Checks if the user needs to be logged in to Coursera, then launches a visible chrome window to
             allow the user to log in manually, then transfers these session cookies to the headless driver.
    Flow:
        1. Navigates to the Coursera home page in the headless driver
        2. Checks for the presense of a page element that indicates if the user is logged in
            - If the user is alredy logged in, this function simply returns.
            - If the user is not alredy logged in, we move on to step 3.
        3. Lanuches a visible driver and clicks the 'log in' button, allowing the user to log in manually
        4. Allows the user 5 minutes to log in, checking on regular intervals for a page elements that 
           indicates login success.
        5. If login success is detected, the visible chrome window is closed, and the visible windows 
           session cookies are transfered to the headless chrome window, and the function returns.
    """
    def perform_login(self):
        """logs into Coursera, if already logged in, does nothing"""

        try:
            self.driver.get("https://www.coursera.org/?authMode=login")
            WebDriverWait(self.driver, 5).until(lambda d: self.home_page.is_logged_in())
            print("\n      ••• ✅" + "\033[1m" + " You're Already logged in to Coursera!" + "\033[0m" + " ✅ •••")
            time.sleep(1)
            return
        except Exception:
            print("\n      ••• ⚠️" + "\033[1m" + " You are not logged in to Coursera!" + "\033[0m" + " ⚠️ •••")
            time.sleep(0.05)
            print("         📌 You will be redirected to log in manually.")
            time.sleep(0.05)
            print("         📌 You have 5 minutes to log in.")
            print("\n")
            spinner = Spinner("      🔄 Opening Visible Window...")
            spinner.start()
            time.sleep(5)
            pass

        
        try:
            # launch a temporary visible driver for manual login
            visible_driver = self._init_driver(headless=False)
            visible_driver.maximize_window()
            temp_home = HomePage(visible_driver)

            # nav to home page with visible driver, click login button
            visible_driver.get("https://www.coursera.org")
            WebDriverWait(visible_driver, 5).until(
                EC.presence_of_element_located(temp_home.LOGIN_SELECTOR)
            )
            spinner.stop()
        except Exception:
            print("   ⚠️ Login page failed to load. Retrying...")

            visible_driver.get("https://www.coursera.org")
            time.sleep(0.2)

        try:
            temp_home.click_login()
        except Exception as e:
            print("   ❌ ERROR: Could not click login button...")
        
        # wait for user to enter login credentials
        try:
            WebDriverWait(visible_driver, 300).until(lambda d: temp_home.is_logged_in())
        except Exception as e:
            sign_in_again = input("   ❌ No login was detected on visible driver, press enter/return to try signing in again: ")
            self.perform_login()
            return
        print("\n")
        spinner = Spinner("      🔄 Transfering cookies to Selenium window...")
        spinner.start()
        try:
            # retrieve cookies and add them to headless driver
            cookies = visible_driver.get_cookies()
            visible_driver.quit()

            self.driver.get("https://www.coursera.org")
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ❌ ERROR: couldnt trasnfer session cookie: {e} to headless driver.")
            self.driver.refresh()
        except Exception as e:
            sign_in_again = input("   ❌ Failed to retrieve cookies, press enter/return to try signing in again: ")
            self.perform_login()
            return
        spinner.stop()

        if self.cinamode:
            os.system('cls' if os.name == 'nt' else 'clear')

        
        print("\n\n      ••• ✅" + "\033[1m" + " Login Successful!" + "\033[0m" + " ✅ •••")

        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.home_page.PROFILE_BUTTON_SELECTOR)
            )
            # reinitialize home pagein case cookies changed session state
            self.home_page = HomePage(self.driver)
            time.sleep(1)
        except Exception as e:
            sign_in_again = print(f"   ❌ ERROR: Could not transfer login to headless driver: {e}")
            self.perform_login()
            return

    """
    Function: nav_to_admin()
    Purpose: Helper function for navigating the headless chrome driver to the 'Educator Admin' dashboard.
    Flow:
        1. Attempts to navigate to the 'Educator Admin' link, which should be universla for all
           CU Coursera Administraton
    """
    def nav_to_admin(self):
        """navigates from the home page to the educator admin dashboard"""
        try:
            self.driver.get(self.admin_dashboard_url)
        except:
            print("\n   ❌ ERROR: Selenium failed to navigate to Educator Admin dashboard.\n ••• Coudln't find page elements to click •••")

        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(CoursePage.TABLE_BODY_LOCATOR)
            )
        except:
            print("\n   ❌ ERROR: Selenium failed to locate the Course Section table.")
    

    """
    Function: main_flow()
    Purpose: The primary function of this class, which handles the entire data scraping flow from start to finish.
        1. Calls perform_login() to allow the user to manually log in to their Coursera Admin account, allowing the
           headless driver access to the user account.
        2. Navigates the user to their 'Educator Admit' course overview dashbaord, and prints a list of predefined 
           course titles that are avialable for scraping which are defined in the 'courses' list.
        3. The user selects and confirms the indices of the courses they'd like to scrape grades from.
        4. For each selected CSCA course title that the user selected, the process_single_course(course name) 
           function is called, passing in the selected course title.
    """
    def main_flow(self):
        self.perform_login()

        self.nav_to_admin()

        try:

            print("\n      ••• 🎯" + "\033[1m" + " Navigation to Educator Admin Dashboard successful!" + "\033[0m" + " 🎯 •••")
            time.sleep(1)

            print("\n ----------------------  ✨" + "\033[1m" + " Available  Courses" + "\033[0m" + " ✨  ---------------------- ")
            time.sleep(0.05)
            for i, course in enumerate(self.course_list, start=1):
                print(f"       " + "\033[1m" + f"{i}." + "\033[0m" + f" {course}")
                time.sleep(0.05)
            print(" ------------------------------------------------------------------------")
            time.sleep(1)
            choice = input("\n   🟢 " + "\033[1m" + "Enter list indices of courses to scrape (e.g. 1,2,5): " + "\033[0m")
            validate_choice = input(f"   🟢 Confirm your selection of '{choice}' by pressing enter/return,\n   🟡 or enter your revised selection: ")
            if validate_choice != "":
                choice = validate_choice
            courseIndices = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
            selected = [self.course_list[i - 1] for i in courseIndices if 1 <= i <= len(self.course_list)]
            time.sleep(1)
            print("\n -----------------------  ✅" + "\033[1m" + " Selected Courses" + "\033[0m" + " ✅  ----------------------- ")
            for course in selected:
                print(f"      📌 {course}")
                time.sleep(0.05)
            print(" ------------------------------------------------------------------------ ")
            time.sleep(2)
        except Exception as e:
            print(f" Error: Failed to present user with courses for selection: {e}")

        if self.cinamode:
            os.system('cls' if os.name == 'nt' else 'clear')

        queue = selected.copy()
        for course_title in selected:
            try:
                queue.remove(course_title)
                if len(queue) > 0:
                    print("\n      ✅ " + "\033[1m" + "Course Queue:" + "\033[0m")
                    time.sleep(0.05)
                    for item in queue:
                        print(f"         🏫 {item}")
                        time.sleep(0.05)
                else:
                    print(f"\n      ••• ✅" + "\033[1m" + f" {course_title} Is The Last Course To Process!" + "\033[0m" + " ✅ ••• ")
                    time.sleep(1)
                self.process_single_course(course_title)
            except Exception as e:
                print(f" Error: Failed to update course queue: {e}")


    """
    Function: process_single_course(course_title)
    Purpose: Handles the navigation and session selection of a single selected CSCA Course.
    Flow:
        1. If not already there, pushes the 'Educator Admin' dashbaord link to bring up the
           Courses Overview page.
        2. Asks the user if they would like to access sessions marked as 'Archived' for this course.
        3. Uses course_page.scrape_courses() to:
            - Search the selected course title in the Course Overview search bar.
            - Scrape the 'sessions' column for resultant row of the Course Overview table.
            - If testing: disregards CSCA prefix requirement for session title
            - If production: only returns sessions prefixed with 'CSCA'
        4. Asks the user to select which resulting course sessions they would like to srape.
        5. For the first session selected under the given course title, the function navigates 
           to that sessions gradebook page and scrapes the Gradebook table column headers.
        6. The full list of available column headers is printed to the user, who is asked to
           select the column to be scraped that will denote a students Honor Quiz completion
        7.
    """
    def process_single_course(self, course_title: str):

        try:
            if self.driver.current_url != self.admin_dashboard_url:
                self.driver.get(self.admin_dashboard_url)
        except Exception as e:
            print(f" Error: Failed to navigate to the admin dashboard: {e}")

        # 1) search for the given course title in the search bar
        try:
            self.course_page.search_courses(course_title)
        except Exception as e:
            print(f" Error: Failed to search for course on the admin dashboard: {e}")

        responses = ["y", 'Y', "n", "N"]
        try:
            search_archive = input("\n   🟢 " + "\033[1m" + "Would you like to also search for Archived sessions? (y/n): " + "\033[0m")
            archive_toggle = False        
            while search_archive not in responses:
                search_archive = input("\n   🟡 Invalid Input: Please enter 'y' or 'n': ")

            validate_choice = input(f"   🟢 Confirm your selection of '{search_archive}' by pressing enter/return,\n   🟡 or enter your revised selection: ")
            if validate_choice in responses:
                search_archive = validate_choice
            if search_archive == "y" or search_archive == "Y":
                archive_toggle = True
        except Exception as e:
            print(f" Error: Failed to present the user with archive toggle selection: {e} ")

        # 2) scrape course sessions from the list of courses that are both 'Live' and prefixed with 'prefix'
        print("\n")
        spinner = Spinner("      🔄 Scraping Course Sessions...")
        spinner.start()
        try:
            return_sessions = self.course_page.scrape_courses(prefix="CSCA", archiveToggle=archive_toggle, isTesting=self.testing) # list of tuples: (course_name, section_name, section_link)

            filtered_sessions = []
            for session in return_sessions:
                (course_name, session_name, link_session, stat) = session
                if course_name == course_title:
                    filtered_sessions.append(session)
        except Exception as e:
            print(f" Error: Failed to scrape and filter selected course sessions: {e}")
        spinner.stop()
        
        status = 'Live'
        prefix = 'CSCA'
        if self.testing:
            status = 'Live or Archived'
            prefix = 'Any Prefix'

        try:
            # 3) prompt user to pick sessions to scrape
            if not filtered_sessions:
                print(f"\n      ⚠️ No sessions were found for '{course_title}' that are:")
                time.sleep(0.05)
                print(f"         📌 Marked as {status}")
                time.sleep(0.05)
                print(f"         📌 prefixed with '{prefix}'")
                return
            
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')

            print(f"\n      ••• 🔍" + "\033[1m" + f"  Current Course: {course_title}" + "\033[0m" + "  🔍 •••")
            time.sleep(1)
            print(f"\n ----------------------  ✨" + "\033[1m" + " Available Sessions" + "\033[0m" + " ✨  ----------------------")
            time.sleep(0.05)
            filtered_sessions.sort(key=lambda session: session[3] != 'Live')
            for i, (c_name, s_name, s_link, s_status) in enumerate(filtered_sessions, start=1):
                if c_name == course_title:
                    status_emoji = "✅" if s_status == "Live" else "📁"
                    print(f"      " + "\033[1m" + f"{i}. 🍎 Session:" + "\033[0m" + f" {s_name}")
                    time.sleep(0.050)
                    print(f"            🏫 Course: {c_name}")
                    time.sleep(0.05)
                    print(f"            {status_emoji} Status: '{s_status}'")
                    time.sleep(0.05)
            print(f" ------------------------------------------------------------------------")
            time.sleep(1)

            valid_input = False
            while valid_input == False:
                choice_input = input("\n   🟢 " + "\033[1m" + f"Enter list indices of sessions to scrape (e.g. 1,3,5): " + "\033[0m")
                sessionIndices = [int(x.strip()) for x in choice_input.split(",") if x.strip().isdigit()]
                discrep_ticker = False
                for dex in sessionIndices:
                    if dex > len(filtered_sessions) + 1 or dex < 1:
                        print("   🟡 Oh No, Your selection was invalid!")
                        print("    Ensure you're properly entering the indices of your selections:\n    '1,2,3,5,10...', '2', etc.")
                        discrep_ticker = True
                        break
                if discrep_ticker == False:
                    valid_input = True

            confirmation = False
            while confirmation == False:
                print("   🟢 Press enter/return to confirm your index selection of:")
                time.sleep(0.05)
                for idx in sessionIndices:
                    print(f"      📌 {filtered_sessions[idx - 1][1]}")
                    time.sleep(0.05)
                confirm_choice_input = input("   🟡 Or enter your revised selection now: ")
                time.sleep(1)

                if confirm_choice_input == "":
                    confirmation = True
                else:
                    sessionIndices = [int(x.strip()) for x in choice_input.split(",") if x.strip().isdigit()]
                    discrep_ticker = False
                    for idx in sessionIndices:
                        if idx > len(filtered_sessions) + 1 or idx < 1 or not idx.isdigit():
                            print("   🟡 Oh No, Your selection was invalid!")
                            print("    Ensure you're properly entering the indices of your selections:\n    '1,2,3,5,10...', '2', etc.")
                            discrep_ticker = True
                            break
                    if discrep_ticker == False:
                        confirmation = True
        except Exception as e:
            print(f" Error: Failed to present user with session options and selection: {e}")

        
        try:
            selected_links = []

            for idx_str in sessionIndices:
                idx = int(idx_str)
                if 1 <= idx <= len(filtered_sessions):
                    selected_links.append(filtered_sessions[idx - 1])

            if not selected_links:
                print(f"\n      ••• ⚠️ No sessions selected for '{course_title}'! ⚠️ •••")
                return
            
            first_session = selected_links[0]
            fs_c, fs_s, fs_link, fs_status = first_session

            self.driver.get(fs_link)
            self.base_page.sleep(2)
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')

            fs_status_emoji = "✅" if fs_status == "Live" else "📁"
    
            print(f"\n      ✨ " + "\033[1m" + f"Now Scraping:" + "\033[0m" + f" {fs_c}")
            print(f"         🍎 Session: {fs_s}")
            print(f"         {fs_status_emoji} Status: {fs_status}")
            time.sleep(1)

            print("\n")
            spinner = Spinner("      🔄 Scraping Gradebook Column Headers...")
            spinner.start()
            headers, required = self.session_page.get_column_headers()
            spinner.stop()

            print(f"\n ----------------------  ✨" + "\033[1m" + " Gradebook  Columns" + "\033[0m" + " ✨  ----------------------")
            time.sleep(0.05)
            for idx, header in enumerate(headers, start=1):
                print(f"      {idx}. {header}")
                time.sleep(0.05)
            time.sleep(0.05)
            print("\n      ••• ✅" + "\033[1m" + " Auto Selected Columns" + "\033[0m" + " ✅ •••")
            for requirement in required:
                print(f"         📌 {requirement}")
                time.sleep(0.05)
            print(f" ------------------------------------------------------------------------")      
            time.sleep(1)     
        except Exception as e:
            print(f" Error: Failed to present user with column headers for their first session selection: {e}")

        try:

            while True:
                honor_input = input("\n   🟢 " + "\033[1m" + f"Enter the list index of the 'Honor Code Quiz' column: " + "\033[0m").strip()
                if honor_input.isdigit() and int(honor_input) in range(1, len(headers) + 1):
                        confirm_honor_input = input("   🟢 Press enter/return to confirm your selection: ")
                        honor_index = int(honor_input) - 1
                        required.append(headers[honor_index])
                        time.sleep(1)
                        break
                else:
                    print("\n   ⚠️ Invalid input. Enter the index left of your chosen column.")
            main_indices = [headers.index(req) for req in required]
            mode_text = "Production Mode" if not self.testing else "Test Mode"
            print(f"\n --------------------  ✨" + "\033[1m" + " Columns to  be Scraped" + "\033[0m" + " ✨  --------------------")
            time.sleep(0.05)
            for header in required:
                print(f"      📌 {header}")
                time.sleep(0.05)
            print(f" ------------------------------------------------------------------------")
            time.sleep(0.05)
            print(f"\n      ⚠️" + "\033[1m" + " Note:" + "\033[0m" + f" Running in {mode_text} requires the following columns:")
            time.sleep(0.05)
            if not self.testing:
                print(f"         1. Student Id")
                time.sleep(0.05)
                print(f"         2. First Name")
                time.sleep(0.05)
                print(f"         3. Last Name")
                time.sleep(0.05)
                print(f"         4. Present Grade")
                time.sleep(0.05)
                print(f"         5. Honor Quiz (chosen by you)")
                time.sleep(1)
            else:
                print(f"         1. Name")
                time.sleep(0.05)
                print(f"         2. Present Grade")
                time.sleep(0.05)
                print(f"         3. Honor Quiz (chosen by you)")
                time.sleep(1)
            while True:
                print("\n      ⚠️ If your list is missing any of these requirements,")
                print("         list the indices of missing requirements (e.g. 1,3),")

                time.sleep(0.05)
                print("\n      ⚠️ If you'd like to remove columns, include 'd' in your response.")
                time.sleep(0.05)
                print("\n      ❓ Response Examples:")
                time.sleep(0.05)
                print("         📌 enter/return")
                time.sleep(0.05)
                print("         📌 '2'")
                time.sleep(0.05)
                print("         📌 '1,3'")
                time.sleep(0.05)
                print("         📌 'd'")
                time.sleep(0.05)
                print("         📌 '1,3,d'")
                time.sleep(0.05)

                built_in_reqs = {"1":"Student Id", "2": "First Name", "3": "Last Name", "4": "Current Grade", "5":"Honor Quiz (chosen by you)"} if not self.testing else {"1":"Name", "2": "Current Grade", "3":"Honor Quiz (chosen by you)"}
                time.sleep(0.05)
                while True:
                    column_fixes = input("\n   🟢 " + "\033[1m" + f"Press enter/return if your selections match: " + "\033[0m")
                    if column_fixes == "":
                        break
                    valid_fix = True
                    for fix in column_fixes.split(","):
                        if fix not in built_in_reqs and fix != "d":
                            print("      ⚠️ Invalid Response. Please try again.")
                            valid_fix = False
                            break
                    if valid_fix == True:
                        break
                time.sleep(0.05)
                if column_fixes == "":
                    break
                else:
                    for fix in column_fixes.split(","):
                        if fix in built_in_reqs:
                            fix_idx = int(fix)
                            print(f"\n      ✅ " + "\033[1m" + f"Beginning process to manually add:" + "\033[0m" + f" {built_in_reqs[fix]}")
                            time.sleep(1) 
                            print(f" ----------------------  ✨" + "\033[1m" + " Gradebook  Columns" + "\033[0m" + " ✨  ----------------------")
                            time.sleep(0.05)
                            for idx, header in enumerate(headers, start=1):
                                print(f"       " + "\033[1m" + f"{idx}. {header}" + "\033[0m")
                                time.sleep(0.05)
                            time.sleep(0.05)
                            print("\n      ••• ✅" + "\033[1m" + " Auto Selected Columns" + "\033[0m" + " ✅ •••")
                            for requirement in required:
                                print(f"      📌 {requirement}")
                                time.sleep(0.05)
                            print(f" ------------------------------------------------------------------------")      
                            time.sleep(1)     

                            while True:
                                replacement_input = input(f"\n   🟢" + "\033[1m" + f" Enter the list index of the new '{built_in_reqs[fix]}' column: " + "\033[0m").strip()
                                if replacement_input.isdigit() and int(replacement_input) in range(1, len(headers) + 1):
                                        confirm_replace_input = input(f"   🟢 Press enter/return to confirm your selection of '{headers[int(replacement_input) - 1]}',\n     Or enter your new selection: ")
                                        if confirm_replace_input == "":
                                            print(f"      ⚠️ This column will be renamed '{built_in_reqs[fix]}' in the resulting Gradebook CSV.")
                                            required.insert(fix_idx - 1, headers[int(replacement_input) - 1])
                                            time.sleep(1)
                                            break
                                        else:
                                            while True:
                                                if confirm_replace_input.isdigit() and int(replacement_input) in range(1, len(headers) + 1):
                                                    print(f"      ⚠️ This column will be renamed '{built_in_reqs[fix]}' in the resulting Gradebook CSV.")
                                                    required.insert(fix_idx - 1, headers[int(replacement_input) - 1])
                                                    time.sleep(1)
                                                    break
                                                else:
                                                    confirm_replace_input = input("      ⚠️ Invalid Input. Please try again: ")
                                            if confirm_replace_input == "":
                                                break
                                            else:
                                                replacement_input = confirm_replace_input
                                                break         
                                else:
                                    replacement_input  = input("\n      ⚠️ Invalid input. Plase try again: ")
                            

                        elif fix == "d":
                            print(f"\n      ✅" + "\033[1m" + " Beginning process to manually remove a selected column!" + "\033[0m")
                            time.sleep(1)
                            print(f"\n --------------------  ✨" + "\033[1m" + " Columns to be Scraped" + "\033[0m" + " ✨  --------------------")
                            time.sleep(0.05)
                            for idx, header in enumerate(required, start = 1):
                                print(f"      " + "\033[1m" + f"{idx}." + "\033[0m" + f" {header}")
                                time.sleep(0.05)
                            print(f" ------------------------------------------------------------------------")
                            time.sleep(1)

                            print("\n      ⚠️ Please ensure that the above list looks like the following or equivelent:")
                            if not self.testing:
                                print(f"         1. Student Id")
                                time.sleep(0.05)
                                print(f"         2. First Name")
                                time.sleep(0.05)
                                print(f"         3. Last Name")
                                time.sleep(0.05)
                                print(f"         4. Current Grade")
                                time.sleep(0.05)
                                print(f"         5. Honor Quiz (chosen by you)")
                                time.sleep(1)
                            else:
                                print(f"         1. Name")
                                time.sleep(0.05)
                                print(f"         2. Current Grade")
                                time.sleep(0.05)
                                print(f"         3. Honor Quiz (chosen by you)")
                                time.sleep(1)

                            max_index = len(required)

                            while True:
                                user_input = input(
                                    "\n   🟢 " + "\033[1m" + f"Select the indices of columns to delete" + "\033[0m" +
                                    f" (1–{max_index}, comma‑separated) or press Enter to cancel deletion: "
                                ).strip()

                                # empty means “delete nothing”
                                if user_input == "":
                                    delete_indices = []
                                    break
                                tokens = [tok.strip() for tok in user_input.split(",")]
                                # validate: every token must be a number in the correct range
                                if all(tok.isdigit() and 1 <= int(tok) <= max_index for tok in tokens):
                                    delete_indices = [int(tok) - 1 for tok in tokens]
                                    break
                                # otherwise, tell them what went wrong and loop again
                                print(
                                    f"      ⚠️ Invalid selection. Please enter numbers between 1 and {max_index}, "
                                    "separated by commas, or press Enter to skip."
                                )

                            for delete_op in delete_indices:
                                print(f"\n      🚩 Removed: {required[delete_op]}")
                                time.sleep(0.05)
                                required.pop(delete_op)
                            
                            print("\n      ✅" + "\033[1m" + " Deletion Complete!" + "\033[0m")
                        else:
                            print(f"      ⚠️ Invalid Change Detected: '{fix}'")
                            print("      ⚠️ Skipping to next Change.")
                    time.sleep(1)
                    print(f"\n ----------------  ✨" + "\033[1m" + " Updated Columns to be Scraped" + "\033[0m" + " ✨  ----------------")
                    time.sleep(0.05)
                    for idx, header in enumerate(required, start = 1):
                        print(f"      " + "\033[1m" + f"{idx}" + "\033[0m" + f". {header}")
                        time.sleep(0.05)
                    print(f" ------------------------------------------------------------------------")
                    time.sleep(1)

                    print("   🟢 " + "\033[1m" + f"Press enter/return if your selections now look coorrect," + "\033[0m")
                    time.sleep(0.05)
                    is_finalized = input("   🟡 or enter any character to configure selections again: ")
                    time.sleep(1)

                    if not is_finalized:
                        break

        except Exception as e:
            print(f" Error: Failed to resolve issues with selected columns: {e}")

        try:    
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')
            required[-1] = "Honor Quiz"
            lowercase_required = [req.lower() for req in required]

            primary_key_index = 0
            if not self.testing:
                try:
                    primary_key_index = lowercase_required.index('student id')
                except ValueError:
                    print("   ❌ ERROR: 'student id' not found among the required columns!")
                    return
            col_selection = (required, primary_key_index, honor_index, main_indices, headers)
            # Now scrape the first session with these columns
            # Then navigate back to the courses page (or do the next link).
            self.scrape_grades_for_session(course_title, fs_s, fs_link, col_selection)
            # For subsequent selected links
        except Exception as e:
            print(f" Error: Failed to scrape first course: {e}")

        for sindex in range(1, len(selected_links)):
            sc_c, sc_s, sc_link = selected_links[sindex]
            self.scrape_grades_for_session(course_title, sc_s, sc_link, col_selection)

        print(f"\n      ••• 🌟" + "\033[1m" + f" Finished scraping for course '{course_title}'!" + "\033[0m" + " 🌟 •••")
        time.sleep(1)

    def scrape_grades_for_session(self, course_name, session_name, link, col_selection):
        if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')
        try:
            time.sleep(0.05)
            print(f"\n\n      🌟 Session: {session_name}")
            print(f"      🌟 Course: {course_name}")
            spinner = Spinner("      🔄 Scraping table grades...")
            spinner.start()

            self.driver.get(link)

            (selected_headers, pk_index, honor_index, main_indices, full_headers) = col_selection
            if self.testing:
                self.session_page.toggle_staff_learners()
        except Exception as e:
            print(f" Error: Failed to load grade table for session: {e}")

        # Wait for table to appear
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
            print(f"   ❌ ERROR: Selenium couldn't find the Gradebook for session:\n  • '{session_name}'\n ••• Skipping •••")
            return

        try:
            rows = self.session_page.get_grade_rows()
        except Exception as e:
            print(f" Error: Failed to Scrape grade rows: {e}")
        if not rows:
            print(f"   ❌ ERROR: No grade rows found for session:\n    • '{session_name}'\n ••• Skipping •••")
            return

        try:
            # filter each row
            data_rows = []
            for row in rows:
                filtered = [row[i] if i < len(row) else "" for i in main_indices]
                data_rows.append(filtered)

            # Build header row from selected indices
            # If in testing mode and there is a "Name" column, split it and add Student ID
            if self.testing:
                name_idx = selected_headers.index("Name")
                # Remove "Name" and insert "First Name" and "Last Name" at its position
                selected_headers.pop(name_idx)
                selected_headers.insert(name_idx, "Last Name")
                selected_headers.insert(name_idx, "First Name")
                # Append Student ID column at the end
                selected_headers.append("Student ID")

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
        except Exception as e:
            print(f" Error: Failed to filter table rows or adjust for test mode: {e}")

        try:
            # Add new column "catalog" from the session_name (assumes session_name.split() returns at least 2 tokens)
            session_title_parts = session_name.split()
            catalog_value = session_title_parts[1] if len(session_title_parts) > 1 else ""
            selected_headers.append("Catalog No.")
            for row in data_rows:
                row.append(catalog_value)
        except Exception as e:
            print(f" Error: Failed to add catalog column: {e}")
        spinner.stop()
        try:

            # final output path
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            output_dir = os.path.join(base_dir, "Coursera-Gradebooks")
            os.makedirs(output_dir, exist_ok=True)
            filename = f"Coursera_Gradebook_{BasePage.sanitize_filename(session_title_parts[1])}_{BasePage.sanitize_filename(session_title_parts[0])}.csv"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(selected_headers)
                writer.writerows(data_rows)
            print(f"      📝" + "\033[1m" + " Saved:" + "\033[0m")
            print(f"         📌 Gradebook: {session_name}")
            print(f"         📌 To: {filepath[0:len(filepath) - len(filename)]}")
            print(f"         📌 Named: {filename}")

            time.sleep(2)
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')
        except Exception as e:
            print(f" Error: Failed to write gradebook to the Coursera-Gradebooks Folder in your root directory: {e}")


def main():

    try:
        # Hide Windows device-level USB errors
        ctypes.windll.kernel32.SetErrorMode(0x0002)
        # Redirect stderr to null device
        sys.stderr = open(os.devnull, 'w')
    except Exception as e:
        pass

    controller = CourseraController()
    controller.main_flow()

if __name__ == "__main__":
    main()