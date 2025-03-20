# integrate.py

import os
import sys
import glob
import csv
import re
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
        print("PHASE: 2 - Data Manipulation")

    def evaluate_grade_discrepancies(self, df):
        """
        Evaluates grade discrepancies for each row of the input DataFrame based on:
        
        - For non-'W' Old Grades (assumed to be one of A, B, C, D, F):
            * If New Grade is the same as Old Grade: no discrepancy.
            * If New Grade is higher than Old Grade: discrepancy and change to New Grade.
            * If New Grade is lower than Old Grade: discrepancy and change to New Grade & not expected.
            
        - For Old Grade 'W':
            * If New Grade is non-'W' and the Policy Quiz is completed (i.e. not empty): discrepancy and change to New Grade.
            * If New Grade is non-'W' but the Policy Quiz is not completed: discrepancy and keep Old Grade.
            
        The function returns a DataFrame that only includes rows with discrepancies. It adds two new columns,
        'Program' (with the value "MEEM") and 'Action' (with the value "Grade Correction"), inserted between
        the 'Career' and 'Old Grade' columns. It also replaces the 'Notes' column with a message describing
        the discrepancy type and removes the 'Policy Quiz' column.
        
        Expected input DataFrame column order:
        ['Student ID', 'Last Name', 'First Name', 'Term', 'Class Number', 'Institution', 
        'Career', 'Old Grade', 'New Grade', 'Class Subject', 'Catalog No.', 'Section', 
        'Notes', 'Policy Quiz']
        
        Returns:
            A DataFrame filtered to only rows with discrepancies and updated as described.
        """
        # Define a mapping for non-W grades (higher numeric value means a better grade)
        grade_mapping = {'A': 10, 'A-': 9, 'B+': 8, 'B': 7, 'B-': 6, 'C+': 6, 'C': 5, 'C-': 4,'D+': 3, 'D': 3, 'D-': 2, 'F': 1}
        
        def process_row(row):
            old_grade = row['Old Grade']
            new_grade = row['New Grade']
            quiz = row['Policy Quiz']
            
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
                    # Check if Honor Quiz (Policy Quiz) is completed:
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
        df_disc['Notes'] = df_disc['discrepancy_message']
        df_disc['New Grade'] = df_disc['newer_grade']
        
        # Insert new columns 'Program' and 'Action' with constant values.
        # We want these columns inserted between 'Career' and 'Old Grade'.
        # First, find the index of the 'Career' column.
        career_index = df_disc.columns.get_loc('Career')
        # Insert 'Program' right after 'Career'
        df_disc.insert(career_index + 1, 'Program', 'MEEM')
        # Insert 'Action' after 'Program'
        df_disc.insert(career_index + 2, 'Action', 'Grade Correction')
        
        # Drop the temporary columns and the 'Policy Quiz' column as requested.
        df_disc.drop(columns=['discrepancy', 'discrepancy_message', 'Policy Quiz', 'newer_grade'], inplace=True)
        
        # Reorder the columns to exactly match the required order:
        desired_order = [
            'Student ID', 'Last Name', 'First Name', 'Term', 'Class Number', 
            'Institution', 'Career', 'Program', 'Action', 'Old Grade', 'New Grade', 
            'Class Subject', 'Catalog No.', 'Section', 'Notes'
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

        # Determine the base directory:
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            base_dir = os.getcwd()

        print("Base directory is:", base_dir)


        # Use that directory in your glob search
        registrar_files = glob.glob(os.path.join(base_dir, "GradeAddReport*.xlsx"))
        if not registrar_files:
            print("No registrar file found with prefix 'GradeAddReport' in this directory.")
        # pick the most recently modified
        registrar_file = max(registrar_files, key=os.path.getmtime)
        print("Using registrar file:", registrar_file)

        # Step 2: Load registrar data
        required_cols = ['emplid','strm','class_nbr','institution','career','incoming grade','subject','catalog','section','message']
        try:
            df_registrar = pd.read_excel(registrar_file, usecols=required_cols)
        except Exception as e:
            print("Error reading registrar file:", e)

        # rename columns to align with the rest of the code
        df_registrar.rename(columns={'emplid': 'Student ID', 'strm': 'Term', 'class_nbr': 'Class Number', 'institution': 'Institution', 'career': 'Career', 'incoming grade': 'Old Grade', 'subject': 'Class Subject', 'catalog': 'Catalog No.', 'section': 'Section', 'message': 'Notes'}, inplace=True)

        # Step 3: discover all coursera CSV files
        coursera_folder = os.path.join(base_dir, "Coursera-Gradebooks")
        if not os.path.isdir(coursera_folder):
            print("No 'Coursera-Gradebooks' folder found at:", coursera_folder)

        csv_files = glob.glob(os.path.join(coursera_folder, "Coursera_Gradebook_*.csv"))
        if not csv_files:
            print("No Coursera Gradebook CSV files found in", coursera_folder)

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

        df_coursera = pd.concat(df_list, ignore_index=True)
        df_coursera.rename(columns={'Present Grade': 'Course Grade', 'catalog': 'Catalog No.'}, inplace=True)

        df_coursera["New Grade"] = df_coursera["Course Grade"].apply(self.calculate_letter_grade)


        # Step 5: Merge on both "Student ID" and "catalog"
        merged_df = pd.merge(df_registrar, df_coursera, on=["Student ID", "Catalog No."], how="inner")
        b3_order = ['Student ID', 'Last Name', 'First Name', 'Term', 'Class Number', 'Institution', 'Career', 'Old Grade', 'New Grade', 'Class Subject', 'Catalog No.', 'Section', 'Notes', 'Policy Quiz']
        merged_df = merged_df[b3_order]
        if merged_df.empty:
            print("Merged data is empty. Possibly no matching 'Student ID' and 'catalog' across files.")
            return

        final_df = self.evaluate_grade_discrepancies(merged_df)
        if final_df.empty:
            print("No grade discrepancies found => no Grade_Corrections.xlsx generated.")
            return
        else:
            # Step 7: write corrections DataFrame to Grade_Corrections.xlsx
            output_file = os.path.join(base_dir, "Grade_Corrections.xlsx")
            try:
                final_df.to_excel(output_file, index=False)
                print("Grade Corrections report generated at:", output_file)
            except Exception as e:
                print("Error writing Grade Corrections report:", e)


# -------------------------------
# Main Execution if run directly
# -------------------------------
if __name__ == "__main__":
    m = LoadData()
    m.main_flow()