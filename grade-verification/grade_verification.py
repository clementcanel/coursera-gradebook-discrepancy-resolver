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