from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from grade_verification.page_objects.base_page import BasePage

class CoursePage(BasePage):
    TABLE_BODY_LOCATOR = (By.CSS_SELECTOR, "tbody.css-11pawnl")
    SHOW_MORE_BUTTON_LOCATOR = (By.XPATH, "//button/span/span[contains(text(),'Show')]")
    # If 'Show' changes, you'll need an updated approach.

    def expand_all_sections(self):
        """
        click all 'Show More' buttons repeatedly until no more remain
        allowing all hidden rows to appear.
        """
        while True:
            buttons = self.driver.find_elements(*self.SHOW_MORE_BUTTON_LOCATOR)
            if not buttons:
                break
            for btn in buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.sleep(1)  # small pause for new rows to render
                except NoSuchElementException:
                    continue

    def scrape_courses(self):
        """
        1) expand all sections.
        2) parse each <tr> in <tbody>.
          - if the first cell has an anchor, it's a new course name.
          - if it's empty, we use the last known course name.
          - the second cell anchor is the section name, if present.
        """
        courses_data = []

        # Expand hidden rows
        self.expand_all_sections()

        # Find the final table body
        table_body = self.driver.find_element(*self.TABLE_BODY_LOCATOR)
        rows = table_body.find_elements(By.TAG_NAME, "tr")

        current_course_name = None

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 2:
                continue  # skip blank rows

            # find a course anchor in the first <td>
            course_anchors = tds[0].find_elements(By.TAG_NAME, "a")
            if course_anchors:
                current_course_name = course_anchors[0].text.strip()

            # find the section name in the second <td>
            section_name = None
            section_anchors = tds[1].find_elements(By.TAG_NAME, "a")
            if section_anchors:
                section_name = section_anchors[0].text.strip()

            # only append if we have a valid course name and section name
            if current_course_name and section_name:
                courses_data.append((current_course_name, section_name))

        return courses_data