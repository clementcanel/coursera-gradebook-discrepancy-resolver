import time
import re
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    test_courses = ["MS-CS CF Sandbox", "MS-CS CF Sandbox 2"]
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
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(self.driver)
    
    def open(self, url: str):
        """navigates the browser to the specified URL"""

        self.driver.get(url)

    def click(self, locator: tuple, timeout=8):
        """waits until the element is present and then clicks it using javaScript"""

        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].click();", element)

    def type(self, locator: tuple, text: str, clear_first=True, timeout=10):
        """waits until the element is visible and then types text into it"""

        elem = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.visibility_of_element_located(locator),
            message=f"Element {locator} not visible within {timeout}s"
        )
        if clear_first:
            elem.clear()
        elem.send_keys(text)

    def is_element_present(self, locator: tuple, timeout=10) -> bool:
        """returns True if the element is present (within the timeout), else False"""

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def scroll_into_view(self, locator: tuple, timeout=10):
        """
        waits for an element to be present and scrolls it into view
        returns the element once scrolled
        """

        element = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
            EC.presence_of_element_located(locator),
            message=f"Element {locator} not present within {timeout}s"
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.sleep(0.5)  # brief pause for scrolling/animation to complete
        return element

    @staticmethod
    def sanitize_filename(s: str) -> str:
        """returns a sanitized version of the given string so its safe for use as a filename"""

        return re.sub(r'[^a-zA-Z0-9_\-]', '_', s)

    def sleep(self, seconds: int):
        """pauses execution for the given number of seconds"""
        
        time.sleep(seconds)