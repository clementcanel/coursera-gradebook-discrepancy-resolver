from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from grade_verification.page_objects.base_page import BasePage

class CoursePage(BasePage):
    TABLE_BODY_LOCATOR = (By.CSS_SELECTOR, "tbody.css-11pawnl")
    SHOW_MORE_BUTTON_LOCATOR = (By.XPATH, "//button/span/span[contains(text(),'Show')]")
    SEARCH_BAR_LOCATOR = (By.XPATH, "//input[@placeholder='Search']")

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

    def search_courses(self, course_name: str):
        """
        Enters the given 'course_name' into the course search bar.
        This triggers the dynamic updating of the course list to only those matching 'course_name'.
        """
        search_bar = self.driver.find_element(*self.SEARCH_BAR_LOCATOR)
        if not search_bar:
            print("Could not locate the course search bar...")
            return
        search_bar.clear()  # clears any existing text
        search_bar.send_keys(course_name)
        self.sleep(1)  # brief pause to let the list update


    def scrape_courses(self, prefix):
        courses_data = [] # holds tuples of course sessions (course_title, session_title, session_link)
        self.expand_all_sections() # expands all hidden sessions

        # finds the table body, and extracts rows
        table_body = self.driver.find_element(*self.TABLE_BODY_LOCATOR)
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        current_course_name = None

        # scrapes data from each course session iteratively
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 2:
                continue
            
            # finds course overview link, extracts the course name
            course_anchors = tds[0].find_elements(By.TAG_NAME, "a")
            if course_anchors:
                current_course_name = course_anchors[0].text.strip()

            section_name = None # holds the current section name
            section_link = None # holds the current section link
            isLive = False # tells us if the section is live or not

            # finds the course section link, and section spans
            section_anchors = tds[1].find_elements(By.TAG_NAME, "a")
            section_spans = tds[1].find_elements(By.TAG_NAME, "span")
            # for each span, determine if any of them contain the text 'Live'
            for span in section_spans:
                if span.text.strip() == "Live":
                    isLive = True
            # if none are marked as Live then there are no more live sessions, and we can return
            if isLive == False:
                return courses_data
            # extracts the section name and link
            if section_anchors:
                section_name = section_anchors[0].text.strip()
                # if the section name is not prefixed with the given prefix then skip this row
                if not section_name.startswith(prefix):
                    print(f"{section_name} did not match {prefix}")
                    continue
                section_link = section_anchors[0].get_attribute("href")

            if current_course_name and section_name:
                courses_data.append((current_course_name, section_name, section_link))

        return courses_data