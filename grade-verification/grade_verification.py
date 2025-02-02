import csv  # Import the CSV module to handle CSV file operations

# Class to represent a student's record, containing personal info and assessments
class StudentRecord:
    def __init__(self, student_id, first_name, last_name, email, assessments):
        # Unique identifier for the student
        self.student_id = student_id
        # Student's first name
        self.first_name = first_name
        # Student's last name
        self.last_name = last_name
        # Student's email address
        self.email = email
        # Dictionary holding the student's assessment data (e.g., quiz grades)
        self.assessments = assessments

# Function to load the gradebook from a CSV file.
# It reads the file, parses each row, and returns a dictionary of StudentRecord objects keyed by student ID.
def load_gradebook(file_path):
    records = {}  # Initialize an empty dictionary to store student records
    # Open the CSV file using a context manager to ensure it closes after reading
    with open(file_path, newline='') as csvfile:
        # Create a CSV dictionary reader to convert rows into dictionaries
        reader = csv.DictReader(csvfile)
        # Iterate over each row in the CSV file
        for row in reader:
            # Extract the student ID from the row; this is used as the key
            student_id = row['Student ID']
            # Extract assessment-related data from the row using a helper function
            assessments = extract_assessments(row)
            # Create a new StudentRecord for the student and add it to the records dictionary
            records[student_id] = StudentRecord(
                student_id,
                row['First Name'],
                row['Last Name'],
                row['Email'],
                assessments
            )
    # Return the complete dictionary of student records
    return records

# Helper function to extract assessment data from a CSV row.
# It iterates through the row's key-value pairs and collects any data where the key contains 'Quiz' or 'Assessment'.
def extract_assessments(row):
    assessments = {}  # Initialize an empty dictionary for assessments
    # Loop through each key-value pair in the row
    for key, value in row.items():
        # Check if the column key includes 'Quiz' or 'Assessment'
        if 'Quiz' in key or 'Assessment' in key:
            # Add this key and its value to the assessments dictionary
            assessments[key] = value
    # Return the dictionary containing only the assessment data
    return assessments

# Function to create dummy registrar data for testing.
# Returns a dictionary with a sample StudentRecord, mimicking what you might receive from the registrar.
def load_dummy_registrar_data():
    dummy_records = {
        # Example record with student ID "12345" and a grade for "Program Policy Quiz"
        "12345": StudentRecord("12345", "Alice", "Smith", "alice@example.com", {"Program Policy Quiz": "1.0"}),
    }
    return dummy_records

# Function to compare two sets of student records: one from Coursera and one from the registrar.
# It identifies discrepancies like missing records and mismatched grades.
def compare_records(coursera_data, registrar_data):
    # Initialize a dictionary to store discrepancies:
    # - 'missing_in_registrar': list of student IDs found in Coursera data but missing in registrar data.
    # - 'grade_mismatches': dictionary mapping student IDs to their differing grade details.
    discrepancies = {'missing_in_registrar': [], 'grade_mismatches': {}}
    
    # Iterate over each student record in the Coursera data
    for student_id, record in coursera_data.items():
        # Check if the student record is missing from the registrar data
        if student_id not in registrar_data:
            discrepancies['missing_in_registrar'].append(student_id)
        else:
            # Retrieve the grade for "Program Policy Quiz" from both data sources
            coursera_grade = record.assessments.get('Program Policy Quiz')
            registrar_grade = registrar_data[student_id].assessments.get('Program Policy Quiz')
            # If the grades do not match, add the details to the grade_mismatches section
            if coursera_grade != registrar_grade:
                discrepancies['grade_mismatches'][student_id] = {
                    'coursera': coursera_grade,
                    'registrar': registrar_grade
                }
    # Return the discrepancies dictionary containing all detected issues
    return discrepancies

# Stub function to handle resolution of discrepancies.
# Currently, it simply prints out the discrepancy; later, you can expand this to include more logic.
def resolve_discrepancy(discrepancy):
    print("Resolving discrepancy:", discrepancy)

# The main block of code that runs when this script is executed directly.
if __name__ == "__main__":
    # Load the Coursera gradebook data from a CSV file.
    # Replace 'path/to/Coursera_Gradebook.csv' with the actual file path of your CSV gradebook.
    coursera_data = load_gradebook('path/to/Coursera_Gradebook.csv')
    
    # Load dummy registrar data for testing comparison functionality.
    registrar_data = load_dummy_registrar_data()
    
    # Compare the Coursera data with the registrar data to find any discrepancies
    discrepancies = compare_records(coursera_data, registrar_data)
    
    # Print out the discrepancies found for review
    print("Discrepancies found:", discrepancies)
    
    # Iterate over the discrepancies and call the resolve function for each type of discrepancy
    for key, value in discrepancies.items():
        resolve_discrepancy({key: value})
