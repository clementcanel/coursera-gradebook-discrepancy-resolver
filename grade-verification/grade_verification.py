import csv 

# Class to represent a student's record, containing personal info and assessments
class StudentRecord:
    def __init__(self, student_id, first_name, last_name, email, assessments):
        self.student_id = student_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.assessments = assessments

# Function to load a gradebook CSV file and return a dictionary of StudentRecord objects keyed by student ID.
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

# Helper function to extract assessment data from a CSV row.
def extract_assessments(row):
    assessments = {}
    for key, value in row.items():
        if 'Quiz' in key or 'Assessment' in key or 'Grade' in key:
            assessments[key] = value
    return assessments

# Function to load dummy registrar data for testing.
def load_dummy_registrar_data():
    dummy_records = {
        "12345": StudentRecord("12345", "Alice", "Smith", "alice@example.com", {"Letter Grade": "B"}),
    }
    return dummy_records

# -------------------------------
# Discrepancy Logic
# -------------------------------
def evaluate_grade_discrepancy(old_grade, new_grade, honor_quiz_completed):
    """
    Compares the old (registrar) and new (Coursera) grades and applies the rules:
    1. If the old grade is A-F (not W):
       - If new grade equals old grade: No discrepancy.
       - If new grade is higher (better): Discrepancy; update to new grade.
       - If new grade is lower (worse): Discrepancy; update to new grade and flag as not expected.
    2. If the old grade is W:
       - If new grade is non-W and honor quiz is completed: Discrepancy; update to new grade.
       - If new grade is non-W and honor quiz is not completed: Discrepancy; keep old grade.
    Returns a dictionary with:
      - 'discrepancy': Boolean flag.
      - 'final_grade': The grade that should be used.
      - 'note': Explanation of the decision.
    """
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
    """
    Compares the new (Coursera) and old (registrar) records:
      - Flags missing registrar records.
      - Applies grade discrepancy rules for matching student IDs.
      
    Returns a dictionary detailing missing records and any grade discrepancies.
    """
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
            # Get honor quiz status (defaulting to 'False' if not present)
            honor_quiz_status = record.assessments.get('Honor Quiz Completed', 'False')
            honor_quiz_completed = honor_quiz_status.lower() in ['true', 'yes', '1']
            result = evaluate_grade_discrepancy(old_grade, new_grade, honor_quiz_completed)
            if result['discrepancy']:
                discrepancies['grade_discrepancies'][student_id] = {
                    'old_grade': old_grade,
                    'new_grade': new_grade,
                    'final_grade': result['final_grade'],
                    'note': result['note']
                }
    return discrepancies
