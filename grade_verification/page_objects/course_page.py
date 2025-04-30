""" FILE OVERVIEW NOTES: course_page.py
    * File: course_page.py (Extends the base_page class)
    * Purpose: A class the houses essential functions for scraping and displaying Course sections for user selection.
        All course_page functions are conducted on the Coursera 'Educator Admin' dashboard at the URL
        'https://www.coursera.org/admin-v2/boulder/home/courses', where a table with the columns: 'Course Name', 
        'sections', 'Enrollments', 'Associated With', stores available courses.
    * Functions:
        1. expand_all_sections: for each row in the table, the 'sections' column has an 'expand sections' dropdown, 
            displaying all course sections, This function iterates through each row of the Course table to expand all 
            section dropdowns.
        2. search_courses: CFs can have up to 60 pages of courses. This function takes a course name and uses the search 
            bar on the 'Educator Admin' dashboard to search for a user slected course, reducing the list of displayed 
            courses for better efficiency.
        3. scrape_courses: Scrapes the 'sections' Column for each row of the Course table after search_courses is run.
            Three settings are utilized for this scrape: 
            - prefix: Set a course title prefix like 'CSCA', and it will only return scraped sections from courses
                      whose name starts with 'CSCA'.
            - archiveToggle: Set to true if the user want's to display 'Archived' course sections for scraping selection.
            - isTesting: Set to true if the program is being run in a test environment (dummy courses/students) and just
                         negates the 'prefix' requirement (test courses don't need to start with 'CSCA')
            * Returns: Returns a list of tuples, each a unique section for the selected course containing the following: 
                - current_course_name: Name of the course for which sections are being scraped
                - section_name: Name of a unique section for the course 'current_course_name'
                - section_link: Link to the section overview page for the section 'section_name'
                - status: A string set to 'Live' if the course is still active, or 'Archived'.  
"""

# External Imports
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Internal Imports
from grade_verification.page_objects.base_page import BasePage

class CoursePage(BasePage):


    """
        * Function: expand_all_sections
        * Purpose: Clicks the 'Show more' button for the first 5 'sections' column cells, showing all course sections.
    """
    def expand_all_sections(self):
        # 1) Find 'Show more' button using the buttons XPath (SHOW_MORE_BUTTON_LOCATOR)
        buttons = self.driver.find_elements(*self.SHOW_MORE_BUTTON_LOCATOR)

        # If no 'Show more' button is found, simply return (only one course section, no expand needed)
        if not buttons:
            return
        
        # 2) For each 'Show more' button, click that button (Only expand the first 5 table rows, everything else is irrelivent)
        expands = 0
        for btn in buttons:
            if expands < 5:
                expands += 1
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                except NoSuchElementException:
                    continue
            else:
                return


    """
        * Function: search_courses
        * Purpose: Enter a given 'course_name' into the course search bar, triggers the dynamic updating of the course list 
          so that those matching 'course_name' are displayed at the top of the course list.
    """
    def search_courses(self, course_name: str):
        # 1) Locate the search bar in the 'Educator Admin' dashboard by its XPath.
        search_bar = self.driver.find_element(*self.SEARCH_BAR_LOCATOR)

        # If no search bar is found print an error, return (most likely not on the 'Educator Admin' dashboard).
        if not search_bar:
            print("Could not locate the course search bar...")
            return
        
        # 2) Clear any text in the search bar, enter the course_name, sleep for 1 second to let the list refresh.
        search_bar.clear()
        search_bar.send_keys(course_name)
        self.sleep(1)


    """
        * Function: scrape_courses
        * Purpose: Enter a required course name prefix, a toggle for displaying 'Archived' courses, and a toggle for negating 
          the prefix requirement, The scrape the first 5 'sections' column cells in the course table, returning a list of 
          section tuples that contain that sections parent course title, section title, section dashboard link, and status.
    """
    def scrape_courses(self, prefix, archiveToggle, isTesting):
        courses_data = []  # holds tuples of course sections (current_course_title, section_title, section_link, status)

        # 1) Expand the 'sections' column for the first 5 course rows in the 'Educator Admin' dashboard course table
        self.expand_all_sections()  # expands all hidden sections

        # 2) Locate the table body by its CSS class, then extract a list of all table rows
        table_body = self.driver.find_element(*self.TABLE_BODY_LOCATOR)
        rows = table_body.find_elements(By.TAG_NAME, "tr")
        current_course_name = None

        # 3) Collect required data from each scraped table row
        for row in rows:
            # Find all table cells for the current row, return if there aren't enough columns to collect required info
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 2:
                continue

            # Extract the current courses name all of this courses section links.
            course_anchors = tds[0].find_elements(By.TAG_NAME, "a")
            if course_anchors:
                current_course_name = course_anchors[0].text.strip()

            section_name = None  # holds the current section name
            section_link = None  # holds the current section link
            isLive = archiveToggle  # tells us if the section is live or archived

            # Find the course section link and any HTML <span> elements.
            section_anchors = tds[1].find_elements(By.TAG_NAME, "a")
            section_spans = tds[1].find_elements(By.TAG_NAME, "span")

            # For each span, determine if any of them contain the text 'Live'
            status = 'Live'
            for span in section_spans:
                if span.text.strip() == "Live":
                    isLive = True
                if span.text.strip() == 'Archived':
                    status = 'Archived'

            # If no <span> elements contain 'Live' then there are no more live sections, return the sections tuple.
            if isLive == False:
                return courses_data
            
            # Extract the current section name and link
            if section_anchors:
                section_name = section_anchors[0].text.strip()
                
                """
                If in test mode, 'CSCA' prefix requirement is nagated.
                 - Test coureses may not have a 'CSCA' prefix
                 - in test mode, prefix is handled automatically in CourseraController.scrape_grades_for_section()
                """
                if not isTesting:
                    # If in production mode, don't append sessions that aren't prefixed with 'CSCA'
                    if not section_name.startswith(prefix):
                        continue
                
                # Extract the string link for the current course session
                section_link = section_anchors[0].get_attribute("href")

                """
                Course session links are always formatted like:
                https://www.coursera.org/teach/<Course Name>/<Session ID>/content/edit
                """
                # Replace '/content/edit/' with '/grading/gradebook/' which is the URL to the session gradebook
                section_link = section_link.replace("/content/edit", "/grading/gradebook")

            # If all required data is successfully extracted, append the session tuple to the list.
            if current_course_name and section_name and section_link:
                courses_data.append((current_course_name, section_name, section_link, status))
        
        # 4) Return the list of course session tuples
        return courses_data