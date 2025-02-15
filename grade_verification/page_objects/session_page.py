from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage

class SessionPage(BasePage):
    # Locator for the 'Grading' tab button.
    GRADING_TAB_BUTTON = (By.XPATH, "//button[.//span[normalize-space(text())='Grading']]")
    
    # Locator for the 'Gradebook Manager' link in the sidebar.
    GRADEBOOK_MANAGER_LINK = (By.XPATH, "//div[contains(@class, 'rc-SideMenu')]//a[contains(text(), 'Gradebook Manager')]")
    
    def go_to_grading_tab(self):
        """Clicks on the 'Grading' tab and waits until the Gradebook Manager link is visible."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Wait up to 15 seconds for the Grading tab to be clickable and get the element.
        grading_tab = WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.element_to_be_clickable(self.GRADING_TAB_BUTTON)
        )
        
        # Scroll the element into view.
        self.driver.execute_script("arguments[0].scrollIntoView(true);", grading_tab)
        self.sleep(0.5)  # Brief pause to allow scrolling/animation to complete.
        
        # Attempt a direct click.
        try:
            grading_tab.click()
        except Exception as e:
            print("Direct click on Grading tab failed, falling back to js_click:", e)
            self.js_click(self.GRADING_TAB_BUTTON, timeout=15)
        
        # Wait until the Gradebook Manager link is visible.
        WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.visibility_of_element_located(self.GRADEBOOK_MANAGER_LINK)
        )
        self.sleep(1)
    
    def open_gradebook_manager(self):
        """Clicks on the 'Gradebook Manager' link in the sidebar and waits for the grade table to load."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        try:
            # Wait up to 15 seconds for the Gradebook Manager link to be present.
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.presence_of_element_located(self.GRADEBOOK_MANAGER_LINK)
            )
        except Exception as e:
            print(f"DEBUG: Could not find Gradebook Manager link.")
            raise e

        # Now attempt to click it with an extended timeout.
        self.js_click(self.GRADEBOOK_MANAGER_LINK, timeout=15)
        self.sleep(3)

    def toggle_staff_learners(self, show_staff=True):
        """
        Toggles the 'Show staff learners' option in the Gradebook Manager.
        Assumes that clicking the gradebook settings button reveals a menu that contains
        the staff learners checkbox and a close button.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Updated locator: rely only on the unique data-e2e attribute.
        settings_button_locator = (By.XPATH, "//button[@data-e2e='gradebook-settings-button']")
        try:
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.element_to_be_clickable(settings_button_locator)
            )
        except Exception as e:
            print(f"DEBUG: Could not find settings button.")
            raise e

        # Click the settings button with an extended timeout.
        self.js_click(settings_button_locator, timeout=15)
        
        # Wait for the staff learners checkbox label to appear.
        staff_checkbox_label_locator = (By.XPATH, "//label[@data-e2e='show-staff-learners-checkbox']")
        WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.visibility_of_element_located(staff_checkbox_label_locator)
        )
        
        # If show_staff is True, click the label to toggle the checkbox.
        if show_staff:
            self.js_click(staff_checkbox_label_locator, timeout=15)
            self.sleep(1)
        
        # Locator for the close button of the settings menu.
        close_button_locator = (By.XPATH, "//button[contains(@class, 'slide-out-close-btn')]")
        WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
            EC.element_to_be_clickable(close_button_locator)
        )
        self.js_click(close_button_locator, timeout=15)
        self.sleep(1)
    
    def get_column_headers(self):
        """Scrapes and returns a list of unique column header texts from the grade table."""
        # Scroll the table horizontally to ensure all columns are loaded.
        try:
            table = self.driver.find_element(By.XPATH, "//table")
            self.driver.execute_script("arguments[0].scrollLeft = arguments[0].scrollWidth;", table)
            self.sleep(2)
        except Exception as e:
            print(f"DEBUG: Could not scroll the table: {e}")
        
        # Use the last header row
        headers_elements = self.driver.find_elements(By.XPATH, "//table//thead/tr[last()]/th")
        all_headers = []
        for i, th in enumerate(headers_elements, start=1):
            # Use JavaScript to get computed innerText
            header_text = self.driver.execute_script("return arguments[0].innerText;", th).strip()
            if header_text:
                all_headers.append(header_text)
        # Deduplicate while preserving order.
        seen = set()
        headers = []
        for header in all_headers:
            if header not in seen:
                seen.add(header)
                headers.append(header)
        return headers
    
    def get_grade_rows(self):
        """Scrapes and returns a list of rows from the grade table.
           Each row is a list of cell texts (empty if the cell is empty).
        """
        try:
            # Wait up to 10 seconds for the table body to be present.
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
            # Extract text from each cell; if a cell is empty, record as empty string.
            row_data = [cell.text.strip() for cell in cells]
            rows.append(row_data)
        return rows