from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grade_verification.page_objects.base_page import BasePage
import os

class SessionPage(BasePage):
    
    # locator for the gradebook manager link in the sidebar
    SETTINGS_BUTTON_LOCATOR = (By.XPATH, "//button[@data-e2e='gradebook-settings-button']")

    CLOSE_BUTTON_LOCATOR = (By.XPATH, "//button[contains(@class, 'slide-out-close-btn')]")

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
    
    def get_column_headers(self, max_scroll_attempts=15, stagnation_limit=3):
        import math

        try:
            table = self.scroll_into_view((By.XPATH, "//table"))
            self.sleep(1)

            scroll_container = self.driver.find_element(By.CSS_SELECTOR, "#hot-root .ht_master .wtHolder")

            scroll_width = self.driver.execute_script("return arguments[0].scrollWidth", scroll_container)
            client_width = self.driver.execute_script("return arguments[0].clientWidth", scroll_container)

            scroll_increment = client_width
            collected_headers = []
            seen = set()

            stagnation_counter = 0
            scroll_position = 0

            for attempt in range(max_scroll_attempts):
                # Grab headers at current scroll
                self.sleep(0.3)
                headers_elements = self.driver.find_elements(By.XPATH, "//table//thead/tr[last()]/th")
                new_headers_this_round = 0

                for th in headers_elements:
                    header_text = self.driver.execute_script("return arguments[0].innerText;", th).strip()
                    if header_text and header_text not in seen:
                        seen.add(header_text)
                        collected_headers.append(header_text)
                        new_headers_this_round += 1

                if new_headers_this_round == 0:
                    stagnation_counter += 1
                    if stagnation_counter >= stagnation_limit:
                        break
                else:
                    stagnation_counter = 0  # Reset stagnation if we found new stuff

                scroll_position += scroll_increment
                self.driver.execute_script("arguments[0].scrollLeft = arguments[1];", scroll_container, scroll_position)

            # Optionally filter required columns
            required_columns = [
                header for header in collected_headers if header.lower() in (
                    'student id', 'present grade', 'first name', 'last name', 'name'
                )
            ]

            return collected_headers, required_columns

        except Exception as e:
            return [], []

    def get_grade_rows(self):
        """
        Scrapes and returns a complete list of grade rows by scrolling through the table both 
        vertically and horizontally to force all cells (including those hidden due to DOM overflow)
        to render.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Wait for the table body
        try:
            tbody = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table//tbody"))
            )
        except Exception:
            print("Error: Grade table body not found.")
            return []

        # Get the container controlling scrolling.
        container = self.driver.find_element(By.CSS_SELECTOR, "#hot-root .ht_master .wtHolder")
        
        # Get container dimensions
        scroll_width = self.driver.execute_script("return arguments[0].scrollWidth;", container)
        client_width = self.driver.execute_script("return arguments[0].clientWidth;", container)
        scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
        client_height = self.driver.execute_script("return arguments[0].clientHeight;", container)
        
        # Use 80% of the client height for vertical increment (to keep slight overlap)
        vertical_increment = max(50, int(client_height * 0.8))
        vertical_positions = list(range(0, int(scroll_height - client_height) + 1, vertical_increment))
        if vertical_positions[-1] != int(scroll_height - client_height):
            vertical_positions.append(int(scroll_height - client_height))
        
        # For horizontal scrolling, using a 150px increment to ensure every column is rendered.
        horizontal_increment = 750
        horizontal_positions = list(range(0, int(scroll_width - client_width) + 1, horizontal_increment))
        if horizontal_positions:
            if horizontal_positions[-1] != int(scroll_width - client_width):
                horizontal_positions.append(int(scroll_width - client_width))
        else:
            horizontal_positions = [0]

        # Dictionary to gather rows: {row_index: {col_index: cell_text}}
        all_rows = {}

        # Loop over vertical positions
        for v_pos in vertical_positions:
            self.driver.execute_script("arguments[0].scrollTop = arguments[1];", container, v_pos)
            
            # Nested loop for horizontal positions
            for h_pos in horizontal_positions:
                self.driver.execute_script("arguments[0].scrollLeft = arguments[1];", container, h_pos)
                
                # Re-fetch tbody only if necessary
                try:
                    tbody = self.driver.find_element(By.XPATH, "//table//tbody")
                except Exception:
                    continue

                row_elements = tbody.find_elements(By.TAG_NAME, "tr")
                for row in row_elements:
                    try:
                        row_index = int(row.get_attribute("aria-rowindex"))
                    except (TypeError, ValueError):
                        continue
                    if row_index not in all_rows:
                        all_rows[row_index] = {}
                    # Get cells of this row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    for cell in cells:
                        col_index_str = cell.get_attribute("aria-colindex")
                        if not col_index_str:
                            continue
                        try:
                            col_index = int(col_index_str)
                        except ValueError:
                            continue
                        cell_text = cell.text.strip()
                        # Only update if the cell hasn’t been captured yet
                        if col_index not in all_rows[row_index] or not all_rows[row_index][col_index]:
                            all_rows[row_index][col_index] = cell_text

        # Determine the total column count using the wtHider element.
        try:
            wtHider = self.driver.find_element(By.CSS_SELECTOR, "#hot-root .ht_master .wtHolder .wtHider")
            wtHider_width = self.driver.execute_script("return arguments[0].offsetWidth;", wtHider)
            max_col_count = int(wtHider_width / 150)
        except Exception:
            print("Error reading wtHider dimensions, defaulting to 30 columns.")
            max_col_count = 30

        # Reconstruct the rows ensuring every column (1 to max_col_count) has a value
        rows_list = []
        for row_index in sorted(all_rows.keys()):
            row_dict = all_rows[row_index]
            # Build row data with empty string fallback
            row_data = [row_dict.get(col, "") for col in range(1, max_col_count + 1)]
            rows_list.append(row_data)
        
        return rows_list
