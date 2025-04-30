""" FILE OVERVIEW NOTES: coursera_controller.py
    - File: coursera_controller.py
    - Purpose: The primary controller class for all Selenium Scraping opperations:
        1. Initialize Selenium & Chrome Drivers
        2. Perform Login Flow
        3. Navigate Coursera Pages
        4. Scrape and Display Coursera Info (available courses, sections, gradebook columns, etc.)
        5. Generate Course/section Gradebooks as individual .csv files in a new 'Coursera-Gradebooks' Folder
            - Gradebook files follow the naming convetion: 'Coursera_Gradebook_<Catalog No.>_CSCA.csv'
"""

# System Imports
import os, csv, sys, ctypes, time, glob
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppresses Windows Error Logs

# Selenium / Chrome Driver Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Internal imports
from grade_verification.page_objects.course_page import CoursePage
from grade_verification.page_objects.section_page import sectionPage
from grade_verification.page_objects.base_page import BasePage
from grade_verification.page_objects.spinner import Spinner

class CourseraController:

    """
        * Function: __init__()
        * Purpose: Initializes the CourseraController object, which is responsible for controlling
                Selenium for grade scraping
        * Flow:
            1. Initializes chrome driver using the _init_driver() function.
            2. Initializes page objects:
                - base_page: Selenium helper functions, XPaths, Course Lists.
                - course_page: Functions for getting section info including search_courses and 
                            scrape_courses
                - section_page: Functions for Gradebook scraping including toggle_staff_learners, 
                                get_column_headers, and get_grade_rows
            3. Verifies the existance of a valid Registrar Record file.
            4. Asks the user if they want to run in test more or not, then sets settings accordingly.
    """
    def __init__(self):
        # Loading spinner starts to indicate startup
        print("\n")
        spinner = Spinner("      🔄 Booting...")
        spinner.start()

        # 1/2) Attempt to initialize the primary Selenium Chrome Driver and all page class objects
        try:
            # Init the driver in headless mode by default
            self.driver = self._init_driver(headless=True)

            # Init page objects with the current driver
            self.base_page = BasePage(self.driver)
            self.course_page = CoursePage(self.driver)
            self.section_page = sectionPage(self.driver)
        except:
            print(" Error: Failed to initialize a chrome driver!")
        spinner.stop()
        

        print("\n\n -------------------------------------------------------------------------")
        print(" ----  ✨" + "\033[1m" + " Starting Up The CU MS-CS Coursera Gradebook Validator!" + "\033[0m" + "  ✨  ----")
        print(" -------------------------------------------------------------------------")

        # Attempts to determine the directory in which this script is running (varies between executable vs. terminal call)
        try:
            # Determine the base directory as a PyInstaller executable:
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_dir = os.path.dirname(sys.executable)
            else:
                # Determine the base directory in a normal Python environment:
                base_dir = os.getcwd()
        except Exception as e:
            # Failed to find base directory:
            print(f" Error: Failed to locate the directory that this excutable is running from:\n {e}")
        
        # 3) Attempt to find a valid Registrar Grade Record in the base directory
        # - A Registrar Record is valid if it is formatted as an Excel (.xlsx) file and has a name prefixed with 'GradeAddReport'
        try:
            registrar_files = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
            registrar_file =  max(registrar_files, key=os.path.getmtime)
        except Exception as e:
            print(f" Error: Failed to locate a valid registrar file in your base directory: \n {e}")
            registrar_file = ""

        # If no valid Registrar Record is detected, print instructions on how to troubleshoot.
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

        # While no valid Registrar Record is detected, reporompt the user to search again. 
        try:
            while not registrar_file:
                re_check = input("\n   🟢 Please press the return/enter key to re-check for a valid Registrar Record:  ")
                registrar_file = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
                if not registrar_file:
                    print("\n   ⚠️ Failed to find the Registrar Record again...")
                time.sleep(1)
        except Exception as e: 
            print(f" Error: Failed to prompt the user to recheck for Registrar File existance: {e}")

        # Split the Registrar Record path into its parts with a '\' as the delimitor 
        try:
            registrar_parts = registrar_file.split("\\")
        except Exception as e:
            print(f"Failed to split the registrar file path into parts:\n {e}")

        # 4) Ask the user if they are running the program in test or production mode
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

        # Print program specifications based on test mode choice
        try:
            if test_selection == "y":
                self.course_list = self.base_page.test_courses
                self.testing = True

                # If the user is in test mode they will be prompted to select if they want to run in 'log' mode
                # - In 'log' mode, the terminal will not be cleared after major program milestones (for debugging)
                # - In non-log or 'Cinimatic' mode, the terminal will be cleared after major milestones (Cleaner UI/UX)
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

                # Print test mode program specifications
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

                # Print production mode specifications
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

        # Set the 'Educator Admin' dashboard URL (same across all CU Boulder affiliated Coursera admin acounts)
        try:
            self.admin_dashboard_url = "https://www.coursera.org/admin-v2/boulder/home/courses"
        except Exception as e:
            print(f" Error: Failed to set selected sections and admin dashboard URL: {e}")
        move_on_input = input("\n   🟢 Press Enter/Return to begin Sign In: ")

        if self.cinamode:
            os.system('cls' if os.name == 'nt' else 'clear')

    """
        * Function: _init_driver(headless: bool)
        * Purpose: Initializes a chrome driver instance to be used by Selenium for web scraping.
        * Flow:
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

        # 1) Set specifications for new Chrome Driver window.
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

        # 2) Create new Chrome Driver window, loading in with the above specifications.
        try:
            # 'log_path=os.devnull' redirects random/unrelated windows terminal outputs to a null terminal. (Keep UI Clean) 
            service = Service(ChromeDriverManager().install(), log_path=os.devnull)
            driver = webdriver.Chrome(service=service, options=options)
            os.system('cls' if os.name == 'nt' else 'clear')
            driver.implicitly_wait(1) # Lets the driver load in (no wait causes problems)
        except Exception as e:
            print(f" ERROR: Failed to launch chrome driver: {e}")
        
        # Return the newly initialized driver.
        return driver


    """
        * Function: perform_login()
        * Purpose: Checks if the user needs to be logged in to Coursera, then launches a visible chrome window to
                allow the user to log in manually, then transfers these section cookies to the headless driver.
        * Flow:
            1. Navigates to the Coursera home page in the headless driver
            2. Checks for the presense of a page element that indicates if the user is logged in
                - If the user is alredy logged in, this function simply returns.
                - If the user is not alredy logged in, we move on to step 3.
            3. Lanuches a visible driver and clicks the 'log in' button, allowing the user to log in manually
            4. Allows the user 5 minutes to log in, checking on regular intervals for a page elements that 
            indicates login success.
            5. If login success is detected, the visible chrome window is closed, and the visible windows 
            section cookies are transfered to the headless chrome window, and the function returns.
    """
    def perform_login(self):
        # 1/2) Navigate to Coursera Home + Login view
        # - If logged in already, return
        # - Log in manually if not logged in already
        try:
            self.driver.get("https://www.coursera.org")
            WebDriverWait(self.driver, 5).until(lambda d: self.base_page.is_logged_in())
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

            # start loading spinner to indicate new driver initialization
            spinner = Spinner("      🔄 Opening Visible Window...")
            spinner.start()
            time.sleep(5)
            pass

        # 3) Launches new/visible Chrome Driver window and directs to the login window
        try:
            # Launch a temporary visible driver for manual login
            visible_driver = self._init_driver(headless=False)
            visible_driver.maximize_window()
            temp_base = BasePage(visible_driver)

            # Nav to home page / login window
            visible_driver.get("https://www.coursera.org/?authMode=login")
            spinner.stop() # No longer initializing the new driver, stop the loading spinner in the terminal
        except Exception:
            print("   ⚠️ Login page failed to load. Retrying...")
            visible_driver.get("https://www.coursera.org")
            time.sleep(0.2)
        
        # wait 5 minutes for the user to enter login credentials and solve any captchas
        try:
            WebDriverWait(visible_driver, 300).until(lambda d: temp_base.is_logged_in())
        except Exception as e:
            sign_in_again = input("   ❌ No login was detected on visible driver, press enter/return to try signing in again: ")
            self.perform_login()
            return
        
        # New loading spinner while session cookies transfer from the logged-in Driver to the Headless Selenium Driver
        print("\n")
        spinner = Spinner("      🔄 Transfering cookies to Selenium window...")
        spinner.start()

        # Attempt to retrive/load the cookies to the headless driver, and close the visible driver
        try:
            cookies = visible_driver.get_cookies()
            visible_driver.quit()

            self.driver.get("https://www.coursera.org")
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ❌ ERROR: couldnt trasnfer section cookie: {e} to headless driver.")
            self.driver.refresh()
        except Exception as e:
            sign_in_again = input("   ❌ Failed to retrieve cookies, press enter/return to try signing in again: ")
            self.perform_login()
            return
        
        spinner.stop() # Stop the loading spinner in the terminal to indicate cookie transfer completion

        if self.cinamode:
            os.system('cls' if os.name == 'nt' else 'clear')

        
        print("\n\n      ••• ✅" + "\033[1m" + " Login Successful!" + "\033[0m" + " ✅ •••")

        # Reinitialize home page in case cookies changed section state
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(self.base_page.PROFILE_BUTTON_SELECTOR)
            )
            self.base_page = BasePage(self.driver)
            time.sleep(1)
        except Exception as e:
            sign_in_again = print(f"   ❌ ERROR: Could not transfer login to headless driver: {e}")
            self.perform_login()
            return


    """
        * Function: nav_to_admin()
        * Purpose: Helper function for navigating the headless chrome driver to the 'Educator Admin' dashboard.
        * Flow:
            1. Attempts to navigate to the 'Educator Admin' link, which should be universal for all
               CU Coursera Administraton.
            2. Looks for the presence of 'Educator Admin' Courses table to verify successful navigation.
    """
    def nav_to_admin(self):

        # 1) Navigate to the Educator Admin Dashbaord        
        try:
            self.driver.get(self.admin_dashboard_url)
        except:
            print("\n   ❌ ERROR: Selenium failed to navigate to Educator Admin dashboard.\n ••• Coudln't find page elements to click •••")

        # 2) Find course table to verify successful navigation
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(CoursePage.TABLE_BODY_LOCATOR)
            )
        except:
            print("\n   ❌ ERROR: Selenium failed to locate the Course section table.")
    

    """
        * Function: main_flow()
        * Purpose: The primary function of this class, which handles the entire data scraping flow from start to finish.
            1. Calls perform_login() to allow the user to manually log in to their Coursera Admin account, allowing the
            headless driver access to the user account.
            2. Navigates the user to their 'Educator Admit' course overview dashbaord, and prints a list of predefined 
            course titles that are avialable for scraping which are defined in the 'courses' list.
            3. The user selects and confirms the indices of the courses they'd like to scrape grades from.
            4. For each selected CSCA course title that the user selected, the process_single_course(course name) 
            function is called, passing in the selected course title.
    """
    def main_flow(self):

        # 1) Perform user login
        self.perform_login()
        
        # 2) Navigate to 'Educator Admin' Dashboard
        self.nav_to_admin()

        # 3) Present available coureses for user selection / user selects and confirms their selecions.
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

        # 4) For each course processed print out a queue of remaining courses to be scraped
        #  - then call self.process_single_course to begin scrape of the next user slected course
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

                # Begin processing the current course's sessions for course session selection.
                self.process_single_course(course_title)

            except Exception as e:
                print(f" Error: Failed to update course queue: {e}")


    """
        * Function: process_single_course(course_title)
        * Purpose: Handles the navigation and section selection of a single selected CSCA Course.
        * Flow:
            1. If not already there, pushes the 'Educator Admin' dashbaord link to bring up the
            Courses Overview page.
            2. Uses course_page.scrape_courses() to:
                - Search the selected course title in the Course Overview search bar.
                - Scrape the 'sections' column for resultant row of the Course Overview table.
                - If testing: disregards CSCA prefix requirement for section title
                - If production: only returns sections prefixed with 'CSCA'
            3. Asks the user if they would like to access sections marked as 'Archived' for this course.
            4. Asks the user to select which resulting course sections they would like to srape.
            5. For the first section selected under the given course title, the function navigates 
            to that sections gradebook page and scrapes the Gradebook table column headers.
            6. The full list of available column headers is printed to the user, who is asked to
            select the column to be scraped that will denote a students Honor Quiz completion
            7. The user will be presented with their final selections and requirements based on 
            if they're running in test vs production mode, and may reconfigure their selections if needed.
            8. Scrapes the first selected section by calling self.scrape_grades_for_section().
            9. Scrapes gradebooks for all subseqent sections.
    """
    def process_single_course(self, course_title: str):
        
        # 1) Navigate to the 'Educator Admin' dashboard if not already there.
        try:
            if self.driver.current_url != self.admin_dashboard_url:
                self.driver.get(self.admin_dashboard_url)
        except Exception as e:
            print(f" Error: Failed to navigate to the admin dashboard: {e}")

        # 2) Search for the given course title in the search bar
        try:
            self.course_page.search_courses(course_title)
        except Exception as e:
            print(f" Error: Failed to search for course on the admin dashboard: {e}")

        # 3) Ask if the user would like to also see 'Archived' sections from the selected course for selection.
        responses = ["y", 'Y', "n", "N"]
        try:
            search_archive = input("\n   🟢 " + "\033[1m" + "Would you like to also search for Archived sections? (y/n): " + "\033[0m")
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

        # Start a loading spinner while the course_page.scrape_courses() funciton scrapes/extracts a list of valid course section tuples
        print("\n")
        spinner = Spinner("      🔄 Scraping Course sections...")
        spinner.start()

        # 4) the course_page.scrape_courses() funciton scrapes/extracts a list of valid course seciton tuples
        #  - Only sections with a 'course_name' that match the 'course_title' are appended/displayed to the user.
        try:
            return_sections = self.course_page.scrape_courses(prefix="CSCA", archiveToggle=archive_toggle, isTesting=self.testing)

            filtered_sections = []
            for section in return_sections:
                (course_name, section_name, link_section, stat) = section
                if course_name == course_title:
                    filtered_sections.append(section)
        except Exception as e:
            print(f" Error: Failed to scrape and filter selected course sections: {e}")

        spinner.stop() # Stop the spinner since course sessions are done being scraped.
        
        status = 'Live'
        prefix = 'CSCA'
        if self.testing:
            status = 'Live or Archived'
            prefix = 'Any Prefix'

        # Display the sessions in filtered_session to the user to be selected for gradebook scraping.
        try:
            if not filtered_sections:
                print(f"\n      ⚠️ No sections were found for '{course_title}' that are:")
                time.sleep(0.05)
                print(f"         📌 Marked as {status}")
                time.sleep(0.05)
                print(f"         📌 prefixed with '{prefix}'")
                return
            
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')

            print(f"\n      ••• 🔍" + "\033[1m" + f"  Current Course: {course_title}" + "\033[0m" + "  🔍 •••")
            time.sleep(1)


            print(f"\n ----------------------  ✨" + "\033[1m" + " Available sections" + "\033[0m" + " ✨  ----------------------")
            time.sleep(0.05)
            filtered_sections.sort(key=lambda section: section[3] != 'Live')
            for i, (c_name, s_name, s_link, s_status) in enumerate(filtered_sections, start=1):
                if c_name == course_title:
                    status_emoji = "✅" if s_status == "Live" else "📁"
                    print(f"      " + "\033[1m" + f"{i}. 🍎 section:" + "\033[0m" + f" {s_name}")
                    time.sleep(0.050)
                    print(f"            🏫 Course: {c_name}")
                    time.sleep(0.05)
                    print(f"            {status_emoji} Status: '{s_status}'")
                    time.sleep(0.05)
            print(f" ------------------------------------------------------------------------")
            time.sleep(1)


            valid_input = False
            while valid_input == False:
                choice_input = input("\n   🟢 " + "\033[1m" + f"Enter list indices of sections to scrape (e.g. 1,3,5): " + "\033[0m")
                sectionIndices = [int(x.strip()) for x in choice_input.split(",") if x.strip().isdigit()]
                discrep_ticker = False
                for dex in sectionIndices:
                    if dex > len(filtered_sections) + 1 or dex < 1:
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
                for idx in sectionIndices:
                    print(f"      📌 {filtered_sections[idx - 1][1]}")
                    time.sleep(0.05)
                confirm_choice_input = input("   🟡 Or enter your revised selection now: ")
                time.sleep(1)

                if confirm_choice_input == "":
                    confirmation = True
                else:
                    sectionIndices = [int(x.strip()) for x in choice_input.split(",") if x.strip().isdigit()]
                    discrep_ticker = False
                    for idx in sectionIndices:
                        if idx > len(filtered_sections) + 1 or idx < 1 or not idx.isdigit():
                            print("   🟡 Oh No, Your selection was invalid!")
                            print("    Ensure you're properly entering the indices of your selections:\n    '1,2,3,5,10...', '2', etc.")
                            discrep_ticker = True
                            break
                    if discrep_ticker == False:
                        confirmation = True
        except Exception as e:
            print(f" Error: Failed to present user with section options and selection: {e}")

        # 5) Navigate to the first user selected section, scrape its gradebook column headers, print to user for column selection.
        try:
            selected_links = []

            # Compile the sections for all user picks
            for idx_str in sectionIndices:
                idx = int(idx_str)
                if 1 <= idx <= len(filtered_sections):
                    selected_links.append(filtered_sections[idx - 1])
            if not selected_links:
                print(f"\n      ••• ⚠️ No sections selected for '{course_title}'! ⚠️ •••")
                return
            
            # Extract the first section fro the list of selected sections
            first_section = selected_links[0]
            fs_c, fs_s, fs_link, fs_status = first_section

            # Navigate to first section gradebook
            self.driver.get(fs_link)
            self.base_page.sleep(2)
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')

            # Display in the console that column headers for the current section are being scraped
            fs_status_emoji = "✅" if fs_status == "Live" else "📁"
            print(f"\n      ✨ " + "\033[1m" + f"Now Scraping:" + "\033[0m" + f" {fs_c}")
            print(f"         🍎 section: {fs_s}")
            print(f"         {fs_status_emoji} Status: {fs_status}")
            time.sleep(1)
            print("\n")

            # Start up loading spinner to indicate waiting for the Selenium process
            spinner = Spinner("      🔄 Scraping Gradebook Column Headers...")
            spinner.start()

            # Scrape the column headers from the first row of the gradebook table
            headers, required = self.section_page.get_column_headers()

            spinner.stop() # Stop the loading spinner


            # Display the list of available gradebook columns, as well as auto-selected columns based on grade validation requirements.
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
            print(f" Error: Failed to present user with column headers for their first section selection: {e}")

        # 6) Ask the user to select the column header that denotes Honor Code Quiz Completion.
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

            # Display a notice about what the requirements for successfull gradebook validation are, allowing the user to make 
            # modifications to the current column selectsions (Remove/Replace a selected column)
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
                    # If the column selections are already valid, the user presses enter, skipping the whole reconfig flow below
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

                # Break out of the reconfig flow if no edits need to be made
                if column_fixes == "":
                    break

                # Split the user's fix selection and process each fix sequentially
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

        # 8) Attempt to scrape the required columns from the gradebook of the first user selected section
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
            # Now scrape the first section with these columns
            # Then navigate back to the courses page (or do the next link).
            self.scrape_grades_for_section(course_title, fs_s, fs_link, col_selection)
            # For subsequent selected links
        except Exception as e:
            print(f" Error: Failed to scrape first course: {e}")

        # 9) Scrape gradebooks for all subsequent course sessions.
        for sindex in range(1, len(selected_links)):
            sc_c, sc_s, sc_link = selected_links[sindex]
            self.scrape_grades_for_section(course_title, sc_s, sc_link, col_selection)

        print(f"\n      ••• 🌟" + "\033[1m" + f" Finished scraping for course '{course_title}'!" + "\033[0m" + " 🌟 •••")
        time.sleep(1)


    """
        * Function: scrape_grades_for_section(course_name, section_name, link, col_selection)
        * Purpose: Handles the navigation and scraping of individual Course Section Gradebooks.
        * Flow:
            1. Navigate to the Course Section Gradebook link
            2. Locates the gradebook table element, then performs the scrape using self.section_page.scrape_grade_rows()
            3. Constructs the output .csv file, which is a process that differs in production vs. test mode
    """
    def scrape_grades_for_section(self, course_name, section_name, link, col_selection):
        if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')

        # 1) Navigate to the current course sessions gradebook view
        try:
            time.sleep(0.05)
            print(f"\n\n      🌟 section: {section_name}")
            print(f"      🌟 Course: {course_name}")
            spinner = Spinner("      🔄 Scraping table grades...")
            spinner.start()

            self.driver.get(link)

            (selected_headers, pk_index, honor_index, main_indices, full_headers) = col_selection
            if self.testing:
                self.section_page.toggle_staff_learners()
        except Exception as e:
            print(f" Error: Failed to load grade table for section: {e}")

        # Wait for gradebook to appear
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
            print(f"   ❌ ERROR: Selenium couldn't find the Gradebook for section:\n  • '{section_name}'\n ••• Skipping •••")
            return

        # 2) Scrape all rows gradebook for the required columns.
        try:
            rows = self.section_page.get_grade_rows()
        except Exception as e:
            print(f" Error: Failed to Scrape grade rows: {e}")
        if not rows:
            print(f"   ❌ ERROR: No grade rows found for section:\n    • '{section_name}'\n ••• Skipping •••")
            return

        # 3) Tailor the gradebook .csv file depending on product/test mode
        try:
            # Filter each row
            data_rows = []
            for row in rows:
                filtered = [row[i] if i < len(row) else "" for i in main_indices]
                data_rows.append(filtered)

            # Build the header row from selected indices
            # If in testing mode and there is a "Name" column, split it and generate dummy Student ID
            # - Dummy Student IDs are in the format '100000001, 100000002, ...'
            # - Ensure you're test GradeAddReport.xslx file correctly reflects dummy id generation here.
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

        # Add new column "catalog" from the section_name (assumes section_name.split() returns at least 2 tokens)
        try:
            section_title_parts = section_name.split()
            catalog_value = section_title_parts[1] if len(section_title_parts) > 1 else ""
            selected_headers.append("Catalog No.")
            for row in data_rows:
                row.append(catalog_value)
        except Exception as e:
            print(f" Error: Failed to add catalog column: {e}")
        spinner.stop()

        # 3.5) Construct and generate output gradebook .csv file
        try:
            # Final output path
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            # Will generate a new folder called 'Coursera-Gradebooks' for storing generated .csv gradebook files.
            output_dir = os.path.join(base_dir, "Coursera-Gradebooks")
            os.makedirs(output_dir, exist_ok=True)

            # Generates unique file names in the format 'Coursera_Gradebook_<Catalog No.>_CSCA.csv
            filename = f"Coursera_Gradebook_{BasePage.sanitize_filename(section_title_parts[1])}_{BasePage.sanitize_filename(section_title_parts[0])}.csv"
            filepath = os.path.join(output_dir, filename)

            # Generate .csv gradebook file
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(selected_headers)
                writer.writerows(data_rows)
            print(f"      📝" + "\033[1m" + " Saved:" + "\033[0m")
            print(f"         📌 Gradebook: {section_name}")
            print(f"         📌 To: {filepath[0:len(filepath) - len(filename)]}")
            print(f"         📌 Named: {filename}")

            time.sleep(2)
            if self.cinamode:
                os.system('cls' if os.name == 'nt' else 'clear')
        except Exception as e:
            print(f" Error: Failed to write gradebook to the Coursera-Gradebooks Folder in your root directory: {e}")

"""
    * Function: main()
    * Purpose: Call this funciton to test coursera scraping in isolation (No gradebook validation or emailing)
"""
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