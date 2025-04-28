# integrate.py

import os
import sys
import glob
import copy
import csv
import re
import time
import pandas as pd
from openpyxl import Workbook
from openpyxl import load_workbook  # if needed for further manipulations

# -------------------------------
# Loader / Discrepancy Class
# -------------------------------

class LoadData:
    """
    A helper class to illustrate how you might load Coursera and Registrar data
    using an object-oriented approach. Not strictly required if you're using
    the main_flow below, but can be used if you want a more granular approach.
    """

    def __init__(self):
        print("\n -------------------------------------------------------------------------")
        print(" ----  ✨" + "\033[1m" + " Grade scraping Complete! Begining discrepancy flagging." + "\033[0m" + " ✨  ----")
        print(" -------------------------------------------------------------------------")
        time.sleep(2)

    def evaluate_grade_discrepancies(self, df):
        """
        Evaluates grade discrepancies for each row of the input DataFrame based on:
        
        - For non-'W' Old Grades (assumed to be one of A, B, C, D, F):
            * If New Grade is the same as Old Grade: no discrepancy.
            * If New Grade is higher than Old Grade: discrepancy and change to New Grade.
            * If New Grade is lower than Old Grade: discrepancy and change to New Grade & not expected.
            
        - For Old Grade 'W':
            * If New Grade is non-'W' and the Honor Quiz is completed (i.e. not empty): discrepancy and change to New Grade.
            * If New Grade is non-'W' but the Honor Quiz is not completed: discrepancy and keep Old Grade.
            
        The function returns a DataFrame that only includes rows with discrepancies. It adds two new columns,
        'Program' (with the value "MEEM") and 'Action' (with the value "Grade Correction"), inserted between
        the 'Career' and 'Old Grade' columns. It also replaces the 'Notes' column with a message describing
        the discrepancy type and removes the 'Honor Quiz' column.
        
        Expected input DataFrame column order:
        ['Student ID', 'Last Name', 'First Name', 'Term', 'Class Number', 'Institution', 
        'Career', 'Old Grade', 'New Grade', 'Class Subject', 'Catalog No.', 'Section', 
        'Notes', 'Honor Quiz']
        
        Returns:
            A DataFrame filtered to only rows with discrepancies and updated as described.
        """
        # Define a mapping for non-W grades (higher numeric value means a better grade)
        grade_mapping = {'A': 10, 'A-': 9, 'B+': 8, 'B': 7, 'B-': 6, 'C+': 6, 'C': 5, 'C-': 4,'D+': 3, 'D': 3, 'D-': 2, 'F': 1}
        
        def process_row(row):
            old_grade = row['old grade']
            new_grade = row['new grade']
            quiz = row['honor quiz']
            
            # Case 1: Old Grade is not 'W'
            if old_grade != 'W':
                # If grades are the same, no discrepancy
                if new_grade == old_grade:
                    return pd.Series([False, "", new_grade])
                # Both grades should be in our mapping for comparison
                if old_grade in grade_mapping and new_grade in grade_mapping:
                    if grade_mapping[new_grade] > grade_mapping[old_grade]:
                        return pd.Series([True, 
                            "Discrepancy: New Grade is higher than Old Grade. Change to New Grade (should be validated).", new_grade
                        ])
                    elif grade_mapping[new_grade] < grade_mapping[old_grade]:
                        return pd.Series([True, 
                            "Discrepancy: New Grade is lower than Old Grade. Change to New Grade & Not Expected (must be validated).", new_grade
                        ])
                # If for some reason the grades are not comparable, no discrepancy is assumed
                return pd.Series([True, "ERROR: grades not comparable", new_grade])
            
            # Case 2: Old Grade is 'W'
            else:
                # Only consider discrepancy if New Grade is not 'W'
                if new_grade != 'W':
                    # Check if Honor Quiz (Honor Quiz) is completed:
                    # We treat non-empty (after stripping) as completed.
                    if pd.notna(quiz) and str(quiz).strip() != "":
                        return pd.Series([True, 
                            "Discrepancy: Honor Quiz completed; change from W to New Grade.", new_grade
                        ])
                    else:
                        row["New Grade"] = "W"
                        return pd.Series([True, 
                            "Discrepancy: Honor Quiz not completed; keep Old Grade", "W"
                        ])
                # If for some reason the grades are not comparable, no discrepancy is assumed
                return pd.Series([True, "ERROR: grades not comparable", new_grade])
        
        # Apply the process_row function to each row to determine discrepancy and message
        df[['discrepancy', 'discrepancy_message', 'newer_grade']] = df.apply(process_row, axis=1)
        
        # Filter out rows with no discrepancy
        df_disc = df[df['discrepancy']].copy()
        
        # Replace 'Notes' with the discrepancy message
        df_disc['notes'] = df_disc['discrepancy_message']
        df_disc['new grade'] = df_disc['newer_grade']
        
        # Insert new columns 'Program' and 'Action' with constant values.
        # We want these columns inserted between 'Career' and 'Old Grade'.
        # First, find the index of the 'Career' column.
        career_index = df_disc.columns.get_loc('career')
        # Insert 'Program' right after 'Career'
        df_disc.insert(career_index + 1, 'program', 'MEEM')
        # Insert 'Action' after 'Program'
        df_disc.insert(career_index + 2, 'action', 'grade Correction')
        
        # Drop the temporary columns and the 'Honor Quiz'
        df_disc.drop(columns=['discrepancy', 'discrepancy_message', 'honor quiz', 'newer_grade'], inplace=True)
        
        # Reorder the columns to exactly match the required order:
        desired_order = [
            'student id', 'last name', 'first name', 'term', 'class number', 
            'institution', 'career', 'program', 'action', 'old grade', 'new grade', 
            'class subject', 'catalog no.', 'section', 'notes'
        ]
        df_disc = df_disc[desired_order]
        
        return df_disc

    @staticmethod
    def calculate_letter_grade(course_grade):
        """
        Convert a numeric or percentage string course grade into a letter grade.
        """
        # If the input is a string, remove whitespace and a trailing "%" if present.
        if isinstance(course_grade, str):
            course_grade = course_grade.strip()
            if course_grade.endswith("%"):
                course_grade = course_grade[:-1]
        # Attempt to convert the value to a float.
        try:
            course_grade = float(course_grade)
        except Exception:
            return 'F'  # fallback in case conversion fails

        # Determine letter grade thresholds.
        if course_grade >= 93:
            return 'A'
        elif course_grade >= 90:
            return 'A-'
        elif course_grade >= 86:
            return 'B+'
        elif course_grade >= 83:
            return 'B'
        elif course_grade >= 80:
            return 'B-'
        elif course_grade >= 76:
            return 'C+'
        elif course_grade >= 73:
            return 'C'
        elif course_grade >= 70:
            return 'C-'
        elif course_grade >= 66:
            return 'D+'
        elif course_grade >= 60:
            return 'D'
        else:
            return 'F'

# ------------------------------------------------
# Main Flow for Data Integration and Discrepancies
# ------------------------------------------------
    def main_flow(self):
        """
        Main flow to load and validate grade data and produce a Grade Corrections report.
        
        Steps:
        1. Locate a registrar file in the current directory (filename prefixed with 'GradeAddReport' + .xlsx).
        2. Load registrar data (using pandas) with required columns: 
        ['emplid','institution','career','strm','subject','catalog','section','class_nbr','incoming grade','message']
        3. Find all Coursera Gradebook CSV files in 'Coursera-Gradebooks' folder (matching 'Coursera_Gradebook_*.csv').
        4. Load and combine all such CSVs into one DataFrame (df_coursera).
        5. Merge df_coursera with registrar DataFrame on 'Student ID'.
        6. Compare old grade (from registrar) and 'Letter Grade' (from CSV).
        7. Output any discrepancies to 'Grade_Corrections.xlsx'.
        """

        try:
            # Determine the base directory:
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running in a normal Python environment
                base_dir = os.getcwd()
        except Exception as e:
            print(f" Error: Failed to get the base path: {e}")

        try:
            # Step 1: Find your file as before…
            registrar_files = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
            registrar_file = max(registrar_files, key=os.path.getmtime)
            print(f"\n      📁 " + "\033[1m" + f"Validating Registrar File:" + "\033[0m" + f"\n         📌 {os.path.basename(registrar_file)}")
            required_cols = [
                'emplid','strm','class_nbr','institution',
                'career','incoming grade','subject',
                'catalog','section','message'
            ]
        except Exception as e:
            print(f" Error finding registrar file: {e}")
            raise

        try:
            # Step 2: Read entire sheet (explicitly naming it)
            df = pd.read_excel(registrar_file, sheet_name='CSCA')
            
            # Step 3: Normalize column names in‑place
            df.columns = df.columns.str.strip().str.lower()
            
            # Optional sanity check:
            missing = set(required_cols) - set(df.columns)
            if missing:
                raise KeyError(f"Missing columns after strip/lower: {missing}")
            
            # Step 4: Subset
            df_registrar = df.loc[:, required_cols]
            
            # Now df_registrar should have exactly the 10 cols you asked for.
        except Exception as e:
            print("Error loading registrar file:", e)
            # handle or re‑raise

        try:
            # rename columns to align with the rest of the code
            df_registrar.rename(columns={'emplid': 'student id', 'strm': 'term', 'class_nbr': 'class number', 'institution': 'institution', 'career': 'career', 'incoming grade': 'old grade', 'subject': 'class subject', 'catalog': 'catalog no.', 'section': 'section', 'message': 'notes'}, inplace=True)
            # Step 3: discover all coursera CSV files
            coursera_folder = os.path.join(base_dir, "Coursera-Gradebooks")
            if not os.path.isdir(coursera_folder):
                print("No 'Coursera-Gradebooks' folder found at:", coursera_folder)

            csv_files = glob.glob(os.path.join(coursera_folder, "Coursera_Gradebook_*.csv"))
            if not csv_files:
                print("No Coursera Gradebook CSV files found in", coursera_folder)
        except Exception as e:
            print(f" Error: : {e}")

        try:
            # Step 4: Load and combine all Coursera CSV data into a single DataFrame
            df_list = []
            for csv_file in csv_files:
                try:
                    df_temp = pd.read_csv(csv_file)
                    df_list.append(df_temp)
                except Exception as e:
                    print(f"Error reading {csv_file} => {e}")
            if not df_list:
                print("No valid Coursera CSV data loaded.")
        except Exception as e:
            print("Failed to fetch all scraped gradebooks from your root directory")

        try:
            df_coursera = pd.concat(df_list, ignore_index=True)
            df_coursera.rename(columns={'Present Grade': 'course grade', 'Catalog': 'catalog no.'}, inplace=True)
            df_coursera.columns = df_coursera.columns.str.lower().str.strip()
            df_coursera["new grade"] = df_coursera["course grade"].apply(self.calculate_letter_grade)
        except Exception as e:
            print(f" Error: Failed to rename coursera gradebook columns and calculate letter grade: {e}")

        # Step 5: Merge on both "Student ID" and "catalog"
        try:
            merged_df = pd.merge(df_registrar, df_coursera, on=["student id", "catalog no."], how="inner")
            b3_order = ['student id', 'last name', 'first name', 'term', 'class number', 'institution', 'career', 'old grade', 'new grade', 'class subject', 'catalog no.', 'section', 'notes', 'honor quiz']
            merged_df = merged_df[b3_order]
            if merged_df.empty:
                print("Merged data is empty. Possibly no matching 'Student ID' and 'catalog' across files.")
                return
        except Exception as e:
            print(f" Error: Failed to merge registrar and coursera gradebooks: {e}")
        
        try:
            final_df = self.evaluate_grade_discrepancies(merged_df)
            if final_df.empty:
                print("No grade discrepancies found => no Grade_Corrections.xlsx generated.")
                return
            else:
                # Step 7: write corrections DataFrame to Grade_Corrections.xlsx
                output_file = os.path.join(base_dir, "Grade_Corrections.xlsx")
                past_output_file = copy.deepcopy(output_file)
                try:
                    final_df.to_excel(output_file, index=False)
                    print(f"\n      ✅ " + "\033[1m" + "Grade Corrections report generated at:" + "\033[0m")
                    time.sleep(0.05)
                    print(f"         📌 File: Grade_Corrections.xslx")
                    time.sleep(0.05)
                    print(f"         📌 Directory: {past_output_file}")
                except Exception as e:
                    print("Error writing Grade Corrections report:", e)
        except Exception as e:
            print(f" Error: Failed to evaluate grade discrpanceies and write Grade_Corrections.xlsx flag file: {e}")


# -------------------------------
# Main Execution if run directly
# -------------------------------
if __name__ == "__main__":
    m = LoadData()
    m.main_flow()