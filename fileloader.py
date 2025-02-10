import pandas as pd
import os

def create_separate_files(input_file):
    """
    Reads an Excel file and processes it into separate files based on unique values 
    in a specific column (e.g., course names, departments, or instructors).
    
    Parameters:
    input_file (str): Path to the input Excel file.
    
    Returns:
    None (Creates separate files per category)
    """
    try:
       
        df = pd.read_csv(input_file)

        
        
        # Create separate files for each course
        #for course_name, course_df in df.groupby("Course"):
            #output_filename = f"{course_name.replace(' ', '_')}_grades.xlsx"
            #course_df.to_excel(output_filename, index=False)
            #print(f"Created file: {output_filename}")

    except Exception as e:
        print(f"Error processing file: {e}")


download_folder = "/Users/aniketchauhan/Downloads"  
file_name = "grades.csv"  # Match the exact file name
file_path = os.path.join(download_folder, file_name)

# Check if file exists before processing
if os.path.exists(file_path):
    print(f"Found the file: {file_path}")
    create_separate_files(file_path)
else:
    print(f"Error: File not found at {file_path}. Ensure it is downloaded and the name is correct.")
