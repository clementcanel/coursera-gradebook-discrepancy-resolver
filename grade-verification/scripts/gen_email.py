import smtplib
import ssl
import email

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# You will need to create an app password for this script you can do this at https://myaccount.google.com/apppasswords
# Doing this requires 2 factor authentication to be active on your account, you can activate it at https://myaccount.google.com/signinoptions/twosv

#attachment_names: list of filepaths attachment to attachments in the email leave blank for none
def gen_email(attachment_names):
    smtp_server = "smtp.gmail.com"
    port = 587
    sender_email = "courseratestemail14@gmail.com"
    # This is an app password for the test email we may want to change this in the future
    # towards something like either the users email or an official special email
    password = "vtxu aalz akom sctr"

    context = ssl.create_default_context()

    msg = MIMEMultipart()
    msg["Subject"] = "Automated Grade Discrepancy Results"
    msg["From"] = sender_email
    msg["To"] = sender_email
    body = MIMEText("The following files represent the requested grade changes from the Automated Discrepancy Resolver", "plain")
    msg.attach(body)

    for attachment_name in attachment_names:
        filename = attachment_name
        # Open file in binary mode
        with open(filename, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to send by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )

        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, sender_email, msg.as_string())

    except Exception as e:
        print("Error in sending email: ", e)#we may want some log file in the future
    finally:
        server.quit()


gen_email(["selenium_login.py","couseraWrapper.py"])