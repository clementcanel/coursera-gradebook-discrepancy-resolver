from grade_verification.scripts.coursera_controller import CourseraController
from grade_verification.scripts.data_loader import LoadData
from grade_verification.scripts.emailer import Emailer


if __name__ == "__main__":
    # complete the grade scraping process
    scrape_grades = CourseraController()
    scrape_grades.main_flow()

    # load and verify registrar and coursera grades
    load_data = LoadData()
    load_data.main_flow()

    # automate the sending of file to registrar
    email_to = Emailer()
    email_to.main_flow()