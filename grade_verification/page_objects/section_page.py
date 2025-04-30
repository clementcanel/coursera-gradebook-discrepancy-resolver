""" FILE OVERVIEW NOTES: section_page.py
    - File: section_page.py (Extends base_page class)
    - Purpose: Class for handing section gradebook scraping. Assumes that the Selenium Chrome Driver is on a gradebook page.
    - Functions:
        1. toggle_staff_learners: accesses the gradebook settings menu to toggle 'show staff learners' (only used for testing).
        2. get_column_headers: Scrapes a list of all gradebook column headers.
        3. get_grade_rows: Scrapes the user specified columns for each row in the gradebook.
"""

# External Imports:
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Internal Imports:
from grade_verification.page_objects.base_page import BasePage


class sectionPage(BasePage):
    
    """
        * Function: toggle_staff_learners(show_staff: bool)
        * Purpose: Used in test mode to show staff students in the gradebook (The rest of your development team)
        * Flow:
            1. Attempt to find/click the gradebook table settings button
            2. Attempt to find/click the 'show staff learners' toggle
            3. Attempt to find/click the 'close settings' button to return to the gradebook dashboard.
    """
    def toggle_staff_learners(self, show_staff=True):
        # Attempt to find/click the gradebook table settings button
        try:
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.element_to_be_clickable(self.SETTINGS_BUTTON_LOCATOR)
            )
            self.click(self.SETTINGS_BUTTON_LOCATOR, timeout=15)
        except Exception as e:
            print(f"DEBUG: Could not find settings button.")
            raise e
        
        # Attempt to find/click taff learners checkbox label
        try:
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.visibility_of_element_located(self.STAFF_CHECKBOX_LABEL_LOCATOR)
            )
            # if show_staff is True click the label to toggle the checkbox
            if show_staff:
                self.click(self.STAFF_CHECKBOX_LABEL_LOCATOR, timeout=15)
                self.sleep(1)
        except Exception as e:
            print(f"DEBUG: Could not find 'toggle staff learners' checkbox.")
            raise e
        
        try:    
            WebDriverWait(self.driver, 15, poll_frequency=0.5).until(
                EC.element_to_be_clickable(self.CLOSE_BUTTON_LOCATOR)
            )
            self.click(self.CLOSE_BUTTON_LOCATOR, timeout=15)
            self.sleep(1)
        except Exception as e:
            print(f"DEBUG: Could not find 'close settings' button.")
            raise e
    

    """
        * Function: get_column_headers(max_scroll_attempts: int, stagnation_limit: int)
        * Purpose: Used to navigate the gradebook table (scroll) to scrape and return all column headers.
                   Scrapes incrementally, then scrolls to bring new table column headers into view
        * Flow:
            1. Define the width of the visible table, as well as the table overflow 
                - Columns always have a with of 150px, so you can discern the number of column headers based
                  on the width of the table overflow
            2. Iteratively extracts column headers by scrolling a new portion of the table into view 
               (initializing it in the DOM, making it available to Selenium for extraction)
            3. Step 2 is repeated 15 times, or until three extraction attempts in a row result in no new 
               column headers.
    """
    def get_column_headers(self, max_scroll_attempts=15, stagnation_limit=3):

        try:
            # Scroll the Gradebook table into view
            table = self.scroll_into_view((By.XPATH, "//table"))
            self.sleep(1)

            # Locate the Gradebook table
            scroll_container = self.driver.find_element(*self.GRADEBOOK_SCROLL_CONTAINER_LOCATOR)

            # Define the scroll overflow of the table and width of the visible table
            scroll_width = self.driver.execute_script("return arguments[0].scrollWidth", scroll_container)
            client_width = self.driver.execute_script("return arguments[0].clientWidth", scroll_container)
            
            # will scroll the table in increments of the width of the visible table to bring non-visible columns into the DOM
            scroll_increment = client_width
            collected_headers = []
            seen = set() # track column headers we've already extracted

            # stagnation is defined as a round scraping that yields no new column headers
            stagnation_counter = 0

            # the initial table scroll position is 0
            scroll_position = 0

            # Selenium will attempt to scrape new column headers 15 times, but will quit automatically
            # when it doesn't find any new column header titles 3 times in a row.
            for attempt in range(max_scroll_attempts):
                # Grab headers at current scroll
                self.sleep(0.3)
                headers_elements = self.driver.find_elements(*self.GRADEBOOK_HEADER_ROW_LOCATOR)
                new_headers_this_round = 0

                # Parse the extraction, add it to the list of collected headers if it hasn't been seen before
                for th in headers_elements:
                    header_text = self.driver.execute_script("return arguments[0].innerText;", th).strip()
                    if header_text and header_text not in seen:
                        seen.add(header_text)
                        collected_headers.append(header_text)
                        new_headers_this_round += 1
                
                # The round of header extraction is stagnent if no new titles are extracted.
                if new_headers_this_round == 0:
                    stagnation_counter += 1
                    if stagnation_counter >= stagnation_limit:
                        break
                else:
                    stagnation_counter = 0  # Reset stagnation if we found new stuff

                # Upon completion of the current iteration, the current scroll position is updated and scrolled again.
                scroll_position += scroll_increment
                self.driver.execute_script("arguments[0].scrollLeft = arguments[1];", scroll_container, scroll_position)

            # Curate a list of 'required columns' of column headers that are consistent across all courses/sections
            # and are required for grade validation & discrepancy reporting.
            required_columns = [
                header for header in collected_headers if header.lower() in (
                    'student id', 'present grade', 'first name', 'last name', 'name'
                )
            ]

            # return the full list of all column headers found along with a list of columns flagged as required.
            return collected_headers, required_columns

        except Exception as e:
            print(f"Error: Failed to scrape column headers: {e}")
            return [], []


    """
        * Function: get_grade_rows()
        * Purpose: Scrapes and returns a complete list of grade rows by scrolling through the table both 
                   vertically and horizontally to force all cells (including those hidden due to DOM overflow)
                   to render.
        * Flow:
            1. Verify the presense of the gradebook table.
            2. Locate gradebook scroll container and define table dimensions
            3. Nestedly loop vertically and horizontally over segments of the gradebook to extract row data.
            4. Construct the gradebook table as a list of rows, containing only selected column data.
    """
    def get_grade_rows(self):

        # 1) Verify the presense of the gradebook table
        try:
            tbody = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception:
            print("Error: Grade table body not found.")
            return []


        # 2) Get the container for scrolling the gradebook
        container = self.driver.find_element(*self.GRADEBOOK_SCROLL_CONTAINER_LOCATOR)
        # 2.1) Get container dimensions
        scroll_width = self.driver.execute_script("return arguments[0].scrollWidth;", container)
        client_width = self.driver.execute_script("return arguments[0].clientWidth;", container)
        scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
        client_height = self.driver.execute_script("return arguments[0].clientHeight;", container)
        # 2.2) Use 80% of the client height for vertical increment (to keep slight overlap)
        vertical_increment = max(50, int(client_height * 0.8))
        vertical_positions = list(range(0, int(scroll_height - client_height) + 1, vertical_increment))
        if vertical_positions[-1] != int(scroll_height - client_height):
            vertical_positions.append(int(scroll_height - client_height))
        # 2.3) For horizontal scrolling use a 150px increment to ensure every column is rendered
        horizontal_increment = 750
        horizontal_positions = list(range(0, int(scroll_width - client_width) + 1, horizontal_increment))
        if horizontal_positions:
            if horizontal_positions[-1] != int(scroll_width - client_width):
                horizontal_positions.append(int(scroll_width - client_width))
        else:
            horizontal_positions = [0]
        # Dictionary to gather rows: {row_index: {col_index: cell_text}}
        all_rows = {}


        # 3) Loop over visible vertical sections to collect data for the visible subset of gradebook rows.
        for v_pos in vertical_positions:
            self.driver.execute_script("arguments[0].scrollTop = arguments[1];", container, v_pos)
            
            # 3.1) For each visible subset of rows, Loop over horizontal subsections of the gradebook extract 
            # hidden/required columns for each row.
            for h_pos in horizontal_positions:
                # Reset the table's horizontal scroll position
                self.driver.execute_script("arguments[0].scrollLeft = arguments[1];", container, h_pos)
                
                # Extract all rows in the visible vertical segmant of the gradebook
                row_elements = tbody.find_elements(By.TAG_NAME, "tr")

                # Iterate over each extracted row
                for row in row_elements:
                    # Find the index of the row
                    try:
                        row_index = int(row.get_attribute("aria-rowindex"))
                    except (TypeError, ValueError):
                        continue

                    # initialize the current row's data storage in all_rows
                    if row_index not in all_rows:
                        all_rows[row_index] = {}

                    # Get cells of this row
                    cells = row.find_elements(By.TAG_NAME, "td")

                    # For each cell in the current row
                    for cell in cells:
                        # Extract the index of the column in the gradebook
                        col_index_str = cell.get_attribute("aria-colindex")
                        if not col_index_str:
                            continue
                        try:
                            col_index = int(col_index_str)
                        except ValueError:
                            continue

                        # Append the contents of the current cell to its corresponding row data in all_rows
                        cell_text = cell.text.strip()
                        # Only update if the cell hasn’t been captured yet
                        if col_index not in all_rows[row_index] or not all_rows[row_index][col_index]:
                            all_rows[row_index][col_index] = cell_text

        # Determine the total column count using the wtHider element. (each column is exactly 150px wide)
        try:
            wtHider = self.driver.find_element(*self.GRADEBOOK_OVERFLOW_LOCATOR)
            wtHider_width = self.driver.execute_script("return arguments[0].offsetWidth;", wtHider)
            max_col_count = int(wtHider_width / 150)
        except Exception:
            print("Error reading wtHider dimensions, defaulting to 30 columns.")
            max_col_count = 30

        # 4) Reconstruct the rows ensuring every column (1 to max_col_count) has a value
        rows_list = []
        for row_index in sorted(all_rows.keys()):
            row_dict = all_rows[row_index]
            # Build row data with empty string fallback
            row_data = [row_dict.get(col, "") for col in range(1, max_col_count + 1)]
            rows_list.append(row_data)
        
        return rows_list
