import os
from grade_verification import load_gradebook, load_registrar_data_pd, load_dummy_registrar_data, consolidate_grade_changes
from b3_generator import generate_b3_file

def main():
    coursera_csv_path = "dummy_coursera_data.csv"
    registrar_csv_path = "dummy_registrar_data.csv" 

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
        
        template_path = "B3 Grade Corrections Template new.xlsx"
        output_path = "B3_Grade_Corrections_FINAL.xlsx"
        generate_b3_file(changes, template_path, output_path)
    else:
        print("No Coursera data to process.")

if __name__ == "__main__":
    main()
