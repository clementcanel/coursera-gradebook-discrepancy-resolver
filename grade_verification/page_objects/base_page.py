""" FILE OVERVIEW NOTES: base_page.py
    - File: base_page.py
    - Purpose: The foundation class from which all page objects extend, serving as a hub for all essential
               Coursera XPaths, Selenium helper functions, and available test/production courses
    - Variables:
        1. test_courses: List of course titles that will be presented to the user when running in test mode
        2. courses: List of production courses listed for user selection (can add new courses to this list)
    - Helper Functions:
        1. click: Locates an element using its XPath and clicks on it.
        2. is_element_present: Locates an element using XPath, returns True if found, else False.
        3. scroll_into_view: Provide an elements XPath and it will scroll that element into view if applicable.
        4. sanatize_filename: Standardizes inputted strings for use in generated file names.
        5. sleep: Pause the driver for a specified amount of time before continuing with the program.
    - XPaths:
        1. PROFILE_BUTTON_SELECTOR: The logged in user's profile icon (only present whe user is logged in).
        2. TABLE_BODY_SELECTOR: The CSS selector for the courses table in the 'Educator Admin' Dashboard.
        3. SHOW_MORE_BUTTON_LOCATOR: 'Show More' buttons in the 'Sessions' column cells of the courses table.
        4. SEARCH_BAR_LOCATOR: The Search bar element in the 'Educator Admin' Dashboard used for course name search.
        5. SETTINGS_BUTTON_LOCATOR: Settings button on the 'Section Gradebook' dashboard, used to toggle staff learners.
        6. STAFF_CHECKBOX_LABEL_LOCATORL: Toggle Checkbox for showing staff learners in the gradebook table.
        7. CLOSE_BUTTON_LOCATOR: Button to close 'Section Gradebook' dashboard settings menu.
        8. GRADEBOOK_SCROLL_CONTAINER_LOCATOR: The scrollable container for gradebook tables.
        9. GRADEBOOK_HEADER_ROW_LOCATOR: The first row of the gradebook table, containing column header titles.
        10. GRADEBOOK_OVERFLOW_LOCATOR: The full gradebook table, including non-visible columns, rows, and cells.
"""

# System Imports
import time, re

# Selenium Imports
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    """
        Test & Production Course Lists:
        - Modify these lists to dictate which courses the user is presented with for selection in Test & Production modes.
    """
    test_courses = [
        "MS-CS CF Sandbox", 
        "MS-CS CF Sandbox 2"
    ]
    courses = [
        "Advanced Data Structures, RSA and Quantum Algorithms",
        "Approximation Algorithms and Linear Programming",
        "Applications of Software Architecture for Big Data",
        "Basic Robotic Behaviors and Odometry",
        "Computing, Ethics, and Society Foundations",
        "Data Mining Methods",
        "Data Mining Pipeline",
        "Data Mining Project",
        "Dynamic Programming, Greedy Algorithms",
        "Ethical Issues in AI and Professional Ethics",
        "Ethical Issues in Computing Applications",
        "Fundamentals of Data Visualization",
        "Fundamentals of Software Architecture for Big Data",
        "Introduction to Computer Vision",
        "Introduction to Deep Learning",
        "Introduction to Generative AI",
        "Introduction to Machine Learning: Supervised Learning",
        "Modeling of Autonomous Systems",
        "Network Principles in Practice: Cloud Networking",
        "Network Principles in Practice: Linux Networking",
        "Network Systems Foundations",
        "Object-Oriented Analysis and Design: Foundations & Concepts",
        "Object-Oriented Analysis and Design: Patterns and Principles",
        "Requirement Specifications for Autonomous Systems",
        "Robotic Mapping and Trajectory Generation",
        "Robotic Path Planning and Task Execution",
        "Security & Ethical Hacking: Attacking the Network",
        "Software Architecture Patterns for Big Data",
        "Unsupervised Algorithms in Machine Learning",
        "Verification and Synthesis of Autonomous Systems",
        "When to Regulate? The Digital Divide and Net Neutrality"
    ]
    
    
    """
        Coursera Page Element XPaths:
        - If selenium naviation fails, Coursera UI changes and outdated XPaths are a probable cause
    """
    # Used for Login Flow
    PROFILE_BUTTON_SELECTOR = (By.CSS_SELECTOR, 'button[data-e2e="header-profile"]')

    # Used for Course/Section Selection
    TABLE_BODY_LOCATOR = (By.CSS_SELECTOR, "tbody.css-11pawnl")
    SHOW_MORE_BUTTON_LOCATOR = (By.XPATH, "//button/span/span[contains(text(),'Show')]")
    SEARCH_BAR_LOCATOR = (By.XPATH, "//input[@placeholder='Search']")

    # Used for Section Gradebook Navigation/Selection
    SETTINGS_BUTTON_LOCATOR = (By.XPATH, "//button[@data-e2e='gradebook-settings-button']")
    STAFF_CHECKBOX_LABEL_LOCATOR = (By.XPATH, "//label[@data-e2e='show-staff-learners-checkbox']")
    CLOSE_BUTTON_LOCATOR = (By.XPATH, "//button[contains(@class, 'slide-out-close-btn')]")
    GRADEBOOK_SCROLL_CONTAINER_LOCATOR = (By.CSS_SELECTOR, "#hot-root .ht_master .wtHolder")
    GRADEBOOK_HEADER_ROW_LOCATOR = (By.XPATH, "//table//thead/tr[last()]/th")
    GRADEBOOK_OVERFLOW_LOCATOR = (By.CSS_SELECTOR, "#hot-root .ht_master .wtHolder .wtHider")



    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(self.driver)

    # Helper function to locate and click a page element by XPath
    def click(self, locator: tuple, timeout=8):

        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].click();", element)


    # Helper funciton to determine of an element is present based on XPath
    def is_element_present(self, locator: tuple, timeout=10) -> bool:

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False


    # Helper funciton to scroll non-visible elements into view 
    # - Essential for dynamically rendered elements or click interactions
    def scroll_into_view(self, locator: tuple, timeout=10):

        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.sleep(0.5)  # brief pause for scrolling/animation to complete
        return element

    # Helper function to standardize input strings for use in file names
    @staticmethod
    def sanitize_filename(s: str) -> str:
        """returns a sanitized version of the given string so its safe for use as a filename"""

        return re.sub(r'[^a-zA-Z0-9_\-]', '_', s)

    # Helper function to pause the driver for a specified amount of time before continuing with the program.
    # - Essential for slow-loading essential page elements 
    def sleep(self, seconds: int):
        """pauses execution for the given number of seconds"""
        
        time.sleep(seconds)

    # Helper function to determine of the user is logged in or not.
    def is_logged_in(self) -> bool:
        return self.is_element_present(self.PROFILE_BUTTON_SELECTOR, timeout=5)