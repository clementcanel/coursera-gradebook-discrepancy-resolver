from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage

class SessionPage(BasePage):
    # locator for the 'Grading' tab button
    GRADING_TAB_BUTTON = (By.XPATH, "//button[.//span[normalize-space(text())='Grading']]")
    
    # locator for the 'Gradebook Manager' link in the sidebar
    GRADEBOOK_MANAGER_LINK = (By.XPATH, "//div[contains(@class, 'rc-SideMenu')]//a[contains(text(), 'Gradebook Manager')]")
    
    # base XPath for the main grade table
    # this targets the table with class "htCore" inside the rc-GradebookManager
    # it excludes any table that is inside an ancestor with "ht_clone"
    TABLE_XPATH = ("//div[contains(@class, 'rc-GradebookManager')]//table[contains(@class, 'htCore') "
                   "and not(ancestor::div[contains(@class, 'ht_clone')])]")
    
    # locator for header cells in the first row of the table header
    TABLE_HEADER_LOCATOR = (By.XPATH, TABLE_XPATH + "//thead/tr[1]/th")
    
    # locator for the table body
    TABLE_BODY_LOCATOR = (By.XPATH, TABLE_XPATH + "//tbody")
    
    def go_to_grading_tab(self):
        """clicks on the Grading tab"""
        self.js_click(self.GRADING_TAB_BUTTON)
        self.sleep(2)
    
    def open_gradebook_manager(self):
        """clicks on the Gradebook Manager link in the sidebar"""
        self.js_click(self.GRADEBOOK_MANAGER_LINK)
        self.sleep(3)
    
    def get_column_headers(self):
        """scrapes and returns a list of unique column header texts from the grade table"""
        try:
            # wait up to 20 seconds for the table to appear
            table = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, self.TABLE_XPATH))
            )
            # scroll horizontally so that all columns become visible
            self.driver.execute_script("arguments[0].scrollLeft = arguments[0].scrollWidth;", table)
            self.sleep(2)
        except Exception as e:
            print(f"DEBUG: Could not find or scroll the table: {e}")
            return []
        
        headers_elements = self.driver.find_elements(*self.TABLE_HEADER_LOCATOR)
        all_headers = []
        for th in headers_elements:
            # etract the visible text of the header cell
            header_text = th.text.strip()
            if header_text:
                all_headers.append(header_text)
        # deduplicate while preserving order
        seen = set()
        headers = []
        for header in all_headers:
            if header not in seen:
                seen.add(header)
                headers.append(header)
        return headers
    
    def get_grade_rows(self):
        """scrapes and returns a list of rows from the grade table
           each row is a list of cell texts (empty if the cell is empty)
        """
        try:
            # wait for the table body element to be present
            tbody = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, self.TABLE_BODY_LOCATOR))
            )
        except Exception as e:
            print("Error: Grade table body not found.")
            return []
        
        row_elements = tbody.find_elements(By.TAG_NAME, "tr")
        rows = []
        
        return rows