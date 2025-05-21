import io
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_mail(subject: str, content: str, receiver_address: str, attachment: str | None = None):
    print("📩 Sending email ...")

    # The mail addresses and password
    sender_address = "tomi.trescak@gmail.com"
    sender_pass = os.getenv("MAIL_PASSWORD")

    if sender_pass is None:
        raise RuntimeError(
            "You need to specify sender password in the MAIL_PASSWORD variable")

    # Setup the MIME
    message = MIMEMultipart("alternative")
    message["From"] = sender_address
    message["To"] = receiver_address
    message["Subject"] = subject  # The subject line
    # The body and the attachments for the mail
    message.attach(MIMEText(content, "html"))

    if attachment is not None:
        attachment_stream = io.BytesIO(attachment.encode())

        # Attach the text content as a file
        filename = "report.html"
        attachment_part = MIMEText(
            attachment_stream.getvalue().decode(), 'plain')
        attachment_part.add_header(
            'Content-Disposition', 'attachment', filename=filename)
        message.attach(attachment_part)

    # Create SMTP session for sending the mail
    session = smtplib.SMTP("smtp.gmail.com", 587, None,
                           10)  # use gmail with port
    session.starttls()  # enable security
    # login with mail_id and password
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()

    print("📩 Mail sent!")
