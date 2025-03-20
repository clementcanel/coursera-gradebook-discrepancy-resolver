from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage
import os

class SessionPage(BasePage):
    # locator for the grading tab button
    GRADING_TAB_BUTTON = (By.XPATH, "//button[.//span[normalize-space(text())='Grading']]")
    
    # locator for the gradebook manager link in the sidebar
    GRADEBOOK_MANAGER_LINK = (By.XPATH, "//div[contains(@class, 'rc-SideMenu')]//a[contains(text(), 'Gradebook Manager')]")

    SETTINGS_BUTTON_LOCATOR = (By.XPATH, "//button[@data-e2e='gradebook-settings-button']")

    CLOSE_BUTTON_LOCATOR = (By.XPATH, "//button[contains(@class, 'slide-out-close-btn')]")
    
    def go_to_grading_tab(self):
        """clicks on the grading tab and waits until the gradebook manager link is visible"""

        # wait up to 15 seconds for the grading tab to be clickable and get the element
        grading_tab = WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.element_to_be_clickable(self.GRADING_TAB_BUTTON)
        )
        
        # scroll the element into view
        self.driver.execute_script("arguments[0].scrollIntoView(true);", grading_tab)
        self.sleep(0.5)  # brief pause to allow scrolling/animation to complete
        
        # attempt a direct click
        try:
            grading_tab.click()
        except Exception as e:
            print(e)
            self.click(self.GRADING_TAB_BUTTON, timeout=15)

    
    def open_gradebook_manager(self):
        """clicks on the gradebook manager link in the sidebar and waits for the grade table to load"""
        # wait until the gradebook manager link is visible
        manager_tab = WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.element_to_be_clickable(self.GRADEBOOK_MANAGER_LINK)
        )

        # scroll the element into view
        self.driver.execute_script("arguments[0].scrollIntoView(true);", manager_tab)
        self.sleep(0.5)  # brief pause to allow scrolling/animation to complete

        # attempt a direct click
        try:
            manager_tab.click()
        except Exception as e:
            print(e)
            self.click(self.GRADEBOOK_MANAGER_LINK, timeout=15)

        self.sleep(3)

    def toggle_staff_learners(self, show_staff=True):
        """
        toggles the show staff learners option in the gradebook manager
        assumes that clicking the gradebook settings button reveals a menu that contains
        the staff learners checkbox and a close button
        """

        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.element_to_be_clickable(self.SETTINGS_BUTTON_LOCATOR)
            )
        except Exception as e:
            print(f"DEBUG: Could not find settings button.")
            raise e

        # click the settings button with an extended timeout
        self.click(self.SETTINGS_BUTTON_LOCATOR, timeout=15)
        
        # wait for the staff learners checkbox label to appear
        staff_checkbox_label_locator = (By.XPATH, "//label[@data-e2e='show-staff-learners-checkbox']")
        WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.visibility_of_element_located(staff_checkbox_label_locator)
        )
        
        # if show_staff is True click the label to toggle the checkbox
        if show_staff:
            self.click(staff_checkbox_label_locator, timeout=15)
            self.sleep(1)
                
        WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.element_to_be_clickable(self.CLOSE_BUTTON_LOCATOR)
        )
        self.click(self.CLOSE_BUTTON_LOCATOR, timeout=15)
        self.sleep(1)
    
    def get_column_headers(self):
        try:
            # use the scroll_into_view method to scroll the table
            self.scroll_into_view((By.XPATH, "//table"))
            self.sleep(2)
        except Exception as e:
            print(f"DEBUG: Could not scroll the table: {e}")
        headers_elements = self.driver.find_elements(By.XPATH, "//table//thead/tr[last()]/th")
        all_headers = []
        for i, th in enumerate(headers_elements, start=1):
            header_text = self.driver.execute_script("return arguments[0].innerText;", th).strip()
            if header_text:
                all_headers.append(header_text)
        seen = set()
        headers = []
        for header in all_headers:
            if header not in seen:
                seen.add(header)
                headers.append(header)
        return headers
    
    def get_grade_rows(self):
        """
        scrapes and returns a list of rows from the grade table
        each row is a list of cell texts (empty if the cell is empty)
        """
        try:
            # wait up to 10 seconds for the table body to be present
            tbody = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception as e:
            print("Error: Grade table body not found.")
            return []
        
        row_elements = tbody.find_elements(By.TAG_NAME, "tr")
        rows = []
        for row in row_elements:
            cells = row.find_elements(By.TAG_NAME, "td")
            # extract text from each cell, if a cell is empty, record as empty string
            row_data = [cell.text.strip() for cell in cells]
            rows.append(row_data)
        return rows