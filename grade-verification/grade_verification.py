import csv
import pandas as pd
import os

# -------------------------------
# Data Models and CSV Loaders
# -------------------------------
class StudentRecord:
    def __init__(self, student_id, first_name, last_name, email, assessments):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.assessments = assessments

def load_gradebook(file_path):
    records = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            student_id = row['Student ID']
            assessments = extract_assessments(row)
            records[student_id] = StudentRecord(
                student_id,
                row['First Name'],
                row['Last Name'],
                row['Email'],
                assessments
            )
    return records

def extract_assessments(row):
    assessments = {}
    for key, value in row.items():
        if 'Quiz' in key or 'Assessment' in key or 'Grade' in key:
            assessments[key] = value
    return assessments

def load_registrar_data_pd(file_path):
    records = {}
    try:
        df = pd.read_csv(file_path)
        for index, row in df.iterrows():
            student_id = str(row['emplid'])
            assessments = {
                "Letter Grade": row['incoming grade'],
                "subject": row.get('subject', ''),
                "catalog": row.get('catalog', ''),
                "section": row.get('section', ''),
                "class_nbr": row.get('class_nbr', '')
            }
            records[student_id] = StudentRecord(
                student_id,
                row.get('first_name', ''),
                row.get('last_name', ''),
                row.get('email', ''),
                assessments
            )
    except Exception as e:
        print("Error loading registrar data via pandas:", e)
    return records

def load_dummy_registrar_data():
    dummy_records = {
        "12345": StudentRecord("12345", "Alice", "Smith", "alice@example.com", {"Letter Grade": "B"}),
    }
    return dummy_records
# -------------------------------
# Discrepancy Logic
# -------------------------------
def evaluate_grade_discrepancy(old_grade, new_grade, honor_quiz_completed):
    if old_grade != 'W':
        if new_grade == old_grade:
            return {'discrepancy': False, 'final_grade': old_grade, 'note': 'No change; grades are the same.'}
        else:
            grade_values = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
            if new_grade not in grade_values or old_grade not in grade_values:
                return {'discrepancy': True, 'final_grade': new_grade, 'note': 'Unrecognized grade format.'}
            if grade_values[new_grade] > grade_values[old_grade]:
                return {'discrepancy': True, 'final_grade': new_grade, 'note': 'New grade is higher; validate improvement.'}
            else:
                return {'discrepancy': True, 'final_grade': new_grade, 'note': 'New grade is lower; not expected; validate.'}
    else:
        if new_grade != 'W':
            if honor_quiz_completed:
                return {'discrepancy': True, 'final_grade': new_grade, 'note': 'Honor quiz completed; update grade.'}
            else:
                return {'discrepancy': True, 'final_grade': old_grade, 'note': 'Honor quiz not completed; keep W.'}
        else:
            return {'discrepancy': False, 'final_grade': old_grade, 'note': 'No change; both grades are W.'}

def compare_records(coursera_data, registrar_data):
    discrepancies = {
        'missing_in_registrar': [],
        'grade_discrepancies': {}
    }
    for student_id, record in coursera_data.items():
        if student_id not in registrar_data:
            discrepancies['missing_in_registrar'].append(student_id)
        else:
            old_grade = registrar_data[student_id].assessments.get('Letter Grade')
            new_grade = record.assessments.get('Letter Grade')
            honor_quiz_completed = 'Honor Quiz' in record.assessments
            result = evaluate_grade_discrepancy(old_grade, new_grade, honor_quiz_completed)
            if result['discrepancy']:
                discrepancies['grade_discrepancies'][student_id] = {
                    'old_grade': old_grade,
                    'new_grade': new_grade,
                    'final_grade': result['final_grade'],
                    'note': result['note'],
                    'record': record  
                }
    return discrepancies

def consolidate_grade_changes(coursera_data, registrar_data):
    """
    Returns a list of grade change dictionaries to be used in generating the final B3 file.
    """
    discrepancies = compare_records(coursera_data, registrar_data)
    changes = []
    for student_id, info in discrepancies['grade_discrepancies'].items():
        record = info['record']
        change = {
            'student_id': student_id,
            'first_name': record.first_name,
            'last_name': record.last_name,
            'course_subject': record.assessments.get('subject', ''),
            'course_number': record.assessments.get('catalog', ''),
            'section': record.assessments.get('section', ''),
            'crn': record.assessments.get('class_nbr', ''),
            'old_grade': info['old_grade'],
            'new_grade': info['new_grade']
        }
        changes.append(change)
    return changes

def resolve_discrepancy(discrepancy):
    print("Resolving discrepancy:", discrepancy)
# -------------------------------
# Main Execution Block (For testing within this module)
# -------------------------------
if __name__ == "__main__":
    # UPDATE WITH REAL PATHS IF AVAILABLE
    coursera_csv_path = "../dummy_coursera_data.csv"
    registrar_csv_path = "path/to/Registrar_Gradebook.csv"

    if os.path.exists(coursera_csv_path):
        coursera_data = load_gradebook(coursera_csv_path)
    else:
        print(f"{coursera_csv_path} not found.")
        coursera_data = None

    try:
        if os.path.exists(registrar_csv_path):
            registrar_data = load_registrar_data_pd(registrar_csv_path)
        else:
            print(f"{registrar_csv_path} not found.")
            registrar_data = load_dummy_registrar_data()
    except Exception as e:
        print("Error loading registrar data:", e)
        registrar_data = load_dummy_registrar_data()

    if coursera_data is not None:
        changes = consolidate_grade_changes(coursera_data, registrar_data)
        print("Consolidated grade changes:", changes)
        # Optionally resolve discrepancies one by one (if needed)
        discrepancies = compare_records(coursera_data, registrar_data)
        for key, value in discrepancies.items():
            resolve_discrepancy({key: value})
    else:
        print("No Coursera data to process.")
