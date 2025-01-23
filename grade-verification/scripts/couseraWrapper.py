# Add page objects below
from page_objects.home_page import HomePage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class CourseraWrapper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        self.driver.implicitly_wait(5)
        self.home_page = HomePage(self.driver)

    def login(self):
        pass


if __name__ == "__main__":
    coursera = CourseraWrapper()
