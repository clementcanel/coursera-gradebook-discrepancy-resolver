import smtplib
import ssl
from email.message import EmailMessage
import os
import certifi
import sys

class Emailer:
    def __init__(self):
        print("PHASE 3 - Automated Emailing")

    def send_email(self, receiver_email):
        smtp_server = "smtp.gmail.com"
        port = 465  # Using SMTP_SSL
        sender_email = "cu.mscs.2025@gmail.com"
        sender_password = "fytb sctd gihu ujai"
        # Create a simple email message
        msg = EmailMessage()
        msg["Subject"] = "Automated Grade Discrepancy Results"
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg.set_content("The following are the requested grade changes provided by the Automated Discrepancy Resolver.")

        # Always attach Grade_Corrections.xlsx from the same directory as this script.
        # Determine the base directory:
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            base_dir = os.getcwd()

        corrections_path = os.path.join(base_dir, "Grade_Corrections.xlsx")
        try:
            with open(corrections_path, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(f.name)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
        except Exception as e:
            print("Error attaching Grade_Corrections.xlsx:", e)

        # Create an SSL context using certifi's certificate bundle
        context = ssl.create_default_context(cafile=certifi.where())

        # Send the email securely using SMTP_SSL
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print("Email sent successfully!")

    def main_flow(self):
        choice = input("Would you like to email these results? (y/n):")
        if choice.lower() != "y":
            return
        receiver_email = input("Please enter the Email you'd like to send this to:")
        print(f"Sending results from cu.mscs.2025@gmail.com to {receiver_email}")
        self.send_email(receiver_email)
        print("Process Complete... You may close this window now.")

if __name__ == "__main__":
    email_to = Emailer()
    email_to.main_flow()