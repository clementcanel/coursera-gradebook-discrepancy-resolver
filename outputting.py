import csv
import pandas as pd
import os

# -------------------------------
# Configurations
# -------------------------------
download_folder = "/Users/aniketchauhan/Documents"  # Your folder path
coursera_csv_path = os.path.join(download_folder, "dummy_coursera_data.csv")
registrar_csv_path = os.path.join(download_folder, "grades.csv")

# -------------------------------
# Load Data
# -------------------------------
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None

# -------------------------------
# Calculate Letter Grade with +/- System
# -------------------------------
def calculate_letter_grade(course_grade):
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

# -------------------------------
# Process Data
# -------------------------------
def extract_relevant_data(coursera_df):
    extracted_data = []
    for _, row in coursera_df.iterrows():
        student_id = row.get('Student ID') or row.get('External Student ID')
        first_name = row.get('First Name', '')
        last_name = row.get('Last Name', '')
        course_grade = row.get('Course Grade', 0)
        letter_grade = calculate_letter_grade(course_grade)
        quiz_score = row.get('Program Policy Quiz', 'N/A')
        
        extracted_data.append({
            "Student ID": student_id,
            "First Name": first_name,
            "Last Name": last_name,
            "Letter Grade": letter_grade,
            "Course Grade": course_grade,
            "Program Policy Quiz Score": quiz_score
        })
    return extracted_data

# -------------------------------
# Main Execution
# -------------------------------
if __name__ == "__main__":
    coursera_df = load_data(coursera_csv_path)
    if coursera_df is not None:
        processed_data = extract_relevant_data(coursera_df)
        output_df = pd.DataFrame(processed_data)
        print(output_df.to_string(index=False))
