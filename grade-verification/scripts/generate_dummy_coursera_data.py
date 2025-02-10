import csv
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()


def random_date():
    return (datetime.utcnow() - timedelta(days=random.randint(1, 365))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def generate_dummy_data(num_students=10):
    headers = [
        # Student Info
        "Anonymized Coursera ID",
        "External Course ID",
        "Term ID",
        "External Student ID",
        "First Name",
        "Last Name",
        "Email",
        "Student ID",
        #
        "Original Assessment Grade: Program Policy Quiz (Passing Threshold: 1.0)",
        "Assessment Grade Override: Program Policy Quiz (Passing Threshold: 1.0)",
        "Submission Time (UTC): Program Policy Quiz",
        "Item Weighting (Percentage): Program Policy Quiz",
        "Points Scored: Program Policy Quiz",
        "Points Total Possible: Program Policy Quiz",
        "Plagiarism Flag Status: Program Policy Quiz",
        "Plagiarism Flag Evidence: Program Policy Quiz",
        "Original Assessment Grade: No Silver Bullet (Passing Threshold: 0.83)",
        "Assessment Grade Override: No Silver Bullet (Passing Threshold: 0.83)",
        "Submission Time (UTC): No Silver Bullet",
        "Item Weighting (Percentage): No Silver Bullet",
        "Points Scored: No Silver Bullet",
        "Points Total Possible: No Silver Bullet",
        "Plagiarism Flag Status: No Silver Bullet",
        "Plagiarism Flag Evidence: No Silver Bullet",
        "Letter Grade",
        "Course Grade",
        "Course Passed",
        "Completed with CC",
        "Present Grade",
    ]

    rows = []
    for _ in range(num_students):
        student_id = random.randint(100000000, 999999999)
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email()
        course_id = fake.uuid4()
        term_id = random.randint(1, 10)
        external_student_id = uuid.uuid4()

        row = [
            student_id,
            course_id,
            term_id,
            external_student_id,
            first_name,
            last_name,
            email,
            student_id,
            round(random.uniform(0.5, 1.0), 2),
            round(random.uniform(0.5, 1.0), 2),
            random_date(),
            10,
            random.randint(5, 10),
            10,
            random.choice(["Flagged", "Not Flagged"]),
            "",
            round(random.uniform(0.5, 1.0), 2),
            round(random.uniform(0.5, 1.0), 2),
            random_date(),
            10,
            random.randint(5, 10),
            10,
            random.choice(["Flagged", "Not Flagged"]),
            "",
            random.choice(["A", "B", "C", "D", "F"]),
            round(random.uniform(60, 100), 2),
            random.choice(["Yes", "No"]),
            random.choice(["Yes", "No"]),
            round(random.uniform(60, 100), 2),
        ]
        rows.append(row)

    with open("dummy_coursera_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    print("Dummy data generated successfully.")


if __name__ == "__main__":
    generate_dummy_data(10)
