import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your Gmail
sender_email = "dnyaneshwarwandhekar4043@gmail.com"
app_password = "iibu fepj rdpa airh"

# User Email
receiver_email = "sarthakwandhekar753@gmail.com"

# Create Message
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = "Test Mail from Python"

body = "Hello,\n\nThis is a test email sent using Python.\n\nThank you!"
message.attach(MIMEText(body, "plain"))

try:
    # Connect to Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)

    # Send Mail
    server.sendmail(sender_email, receiver_email, message.as_string())
    print("Email sent successfully!")

    server.quit()

except Exception as e:
    print("Error:", e)