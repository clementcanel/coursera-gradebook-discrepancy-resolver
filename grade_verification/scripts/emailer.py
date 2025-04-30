""" FILE OVERVIEW NOTES: emailer.py
    - File: emailer.py
    - Purpose: The primary controller class for handling automatic email of the generated discrepancy flag file.
        1. Ask the user if they want to automatically set the generated discrepancy report to the registrar.
        2. Ask the user to enter the email they would like to send the report to.
        3. Send report to user specified email address.
"""


# Imports
import smtplib, ssl, os, certifi, sys, time
from email.message import EmailMessage

class Emailer:


    def __init__(self):
        print("\n -------------------------------------------------------------------------")
        print(" ---------  ✨" + "\033[1m" + f" Registrar Grade Discrepancy Report Complete!" + "\033[0m" + f" ✨  ----------")
        print(" -------------------------------------------------------------------------")
        time.sleep(2)


    """
        * Function: send_email(receiver_email: string)
        * Purpose: Handles the sending of the discrepancy report to the user specified email address.
        * Flow:
            1. Load in default variables and set Email message.
            2. Locate and append the discrepancy report to the Email message.
            3. Create SSL Context and send email using secure port.
    """
    def send_email(self, receiver_email):


        # 1) Set default variables 
        smtp_server = "smtp.gmail.com" # SMTP server set up for sending/recieving with gmail accounts
        port = 465  # Using SMTP_SSL # SMTP open SSL port being used to send the email
        sender_email = "cu.mscs.2025@gmail.com" # Email address sending the discrepancy report
        sender_password = "fytb sctd gihu ujai" # Passkey to allow access to 'cu.mscs.2025@gmail.com'
        # 1.1) Create a simple email message
        msg = EmailMessage()
        msg["Subject"] = "Automated Grade Discrepancy Results"
        msg["From"] = sender_email
        msg["To"] = receiver_email
        try:
            msg.set_content("The following are the requested grade changes provided by the Automated Discrepancy Resolver.")
        except Exception as e:
            print(f" Error: Failed to set message content: {e}")


        # 2) Determine the discrepancy report location:
        try:
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running in a normal Python environment
                base_dir = os.getcwd()
            corrections_path = os.path.join(base_dir, "Grade_Corrections.xlsx")
        except Exception as e:
            print(f" Error: Failed to find the base directory: {e}")
        # 2.1) Read the discrepancy report and attach it to the email to be sent.
        try:
            with open(corrections_path, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(f.name)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)
        except Exception as e:
            print("Error attaching Grade_Corrections.xlsx:", e)


        # 3) Create an SSL context using certifi's certificate bundle
        try:
            context = ssl.create_default_context(cafile=certifi.where())
        except Exception as e:
            print(f" Error: Failed to create SSL Context: {e}")

        # 3.1) Send the email securely using SMTP_SSL
        try:
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
                print("\n      ✅ " + "\033[1m" + f"Email sent successfully!" + "\033[0m")
        except Exception as e:
            print(f" Error: Failed to send email: {e}")


    """
        * Function: main_flow()
        * Purpose: Handles the user interaction of sending the discrepancy report to a user specified email address.
        * Flow:
            1. Ask the user if they want to automatically set the generated discrepancy report to the registrar.
            2. Ask the user to enter the email they would like to send the report to.
            3. Send report to user specified email address.
    """
    def main_flow(self):
        choice = input("\n   🟢" + "\033[1m" + " Would you like to email these results? (y/n):" + "\033[1m")
        if choice.lower() != "y" and choice.lower() != "Y":
            print("\n -------------------------------------------------------------------------")
            print(" ---------  ✨" + "\033[1m" + f"  Process Comlete! You may close this window." + "\033[0m" + f"  ✨  ---------")
            print(" -------------------------------------------------------------------------")
            return
        receiver_email = input("\n   🟢 " + "\033[1m" + f"Enter the receiving Email address:" + "\033[0m")
        print(f"\n      📫 " + "\033[1m" + f"Sending Results:" + "\033[0m")
        time.sleep(0.05)
        print(f"         📌 From: cu.mscs.2025@gmail.com")
        time.sleep(0.05)
        print(f"         📌 To: {receiver_email}")
        self.send_email(receiver_email)
        print("\n -------------------------------------------------------------------------")
        print(" ---------  ✨  " + "\033[1m" + f"Process Comlete! You may close this window." + "\033[0m" + f"  ✨  ---------")
        print(" -------------------------------------------------------------------------")


if __name__ == "__main__":
    email_to = Emailer()
    email_to.main_flow()