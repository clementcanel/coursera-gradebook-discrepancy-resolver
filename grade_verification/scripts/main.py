from grade_verification.scripts.coursera_controller import CourseraController
from grade_verification.scripts.data_loader import LoadData
from grade_verification.scripts.emailer import Emailer

import ctypes
import sys
import os


if __name__ == "__main__":
    try:
        # Hide Windows device-level USB errors
        ctypes.windll.kernel32.SetErrorMode(0x0002)
        # Redirect stderr to null device
        sys.stderr = open(os.devnull, 'w')
    except Exception as e:
        pass

    # complete the grade scraping process
    scrape_grades = CourseraController()
    scrape_grades.main_flow()

    # load and verify registrar and coursera grades
    load_data = LoadData()
    load_data.main_flow()

    # automate the sending of file to registrar
    email_to = Emailer()
    email_to.main_flow()