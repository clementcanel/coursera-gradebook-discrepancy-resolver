from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from grade_verification.page_objects.base_page import BasePage

class CoursePage(BasePage):
    TABLE_BODY_LOCATOR = (By.CSS_SELECTOR, "tbody.css-11pawnl")
    SHOW_MORE_BUTTON_LOCATOR = (By.XPATH, "//button/span/span[contains(text(),'Show')]")

    def expand_all_sections(self):
        while True:
            buttons = self.driver.find_elements(*self.SHOW_MORE_BUTTON_LOCATOR)
            if not buttons:
                break
            for btn in buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                except NoSuchElementException:
                    continue

    def scrape_courses(self):
        courses_data = []
        self.expand_all_sections()
        table_body = self.driver.find_element(*self.TABLE_BODY_LOCATOR)
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        current_course_name = None
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 2:
                continue
            course_anchors = tds[0].find_elements(By.TAG_NAME, "a")
            if course_anchors:
                current_course_name = course_anchors[0].text.strip()
            section_name = None
            section_anchors = tds[1].find_elements(By.TAG_NAME, "a")
            if section_anchors:
                section_name = section_anchors[0].text.strip()
            if current_course_name and section_name:
                courses_data.append((current_course_name, section_name))
        return courses_data