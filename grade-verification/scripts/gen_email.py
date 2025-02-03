import smtplib
import ssl

# You will need to create an app password for this script you can do this at https://myaccount.google.com/apppasswords
# Doing this requires 2 factor authentication to be active on your account, you can activate it at https://myaccount.google.com/signinoptions/twosv

# with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
#      server.login("courseratestemail14@gmail.com", "vtxu aalz akom sctr")

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "courseratestemail14@gmail.com"
password = "vtxu aalz akom sctr"

# Create a secure SSL context
context = ssl.create_default_context()

text = """\
test
testing"""

# ata = MIMEText("atatest", "plain")
# msg = MIMEMultipart()
# msg["Subject"] = "test"
# msg["From"] = sender_email
# msg["To"] = sender_email
# msg[]
# msg.attach(ata)
# Try to log in to server and send email
#msg.as_string()
try:
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, sender_email, text)

except Exception as e:
    # Print any error messages to stdout
    print(e)
finally:
    server.quit()
