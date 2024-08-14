from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import email_setting
import smtplib
import sys
import ssl
import os


class Mailer:
    def __init__(self, to_address: str = None):
        if to_address is not None:
            self.to_address = to_address
        else:
            self.to_address = email_setting.to_address

    def set_to(self, to_address: str):
        self.to_address = to_address

    def get_to(self):
        return self.to_address

    def create_message_body(self, title: str, body: str, attach_file: str = None):
        msg = MIMEMultipart()
        msg["Subject"] = title
        msg["From"] = email_setting.from_address
        msg["To"] = self.to_address
        msg.attach(MIMEText(body))

        if attach_file is not None:
            filename = os.path.basename(attach_file)
            with open(attach_file, 'rb') as f:
                attach = MIMEApplication(f.read())

            attach.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attach)

        return msg

    def send_mail(self, msg: EmailMessage):
        context = ssl.create_default_context()
        # with smtplib.SMTP(email_setting.smtp_host, email_setting.smtp_port) as server:
        with smtplib.SMTP_SSL(email_setting.smtp_host, email_setting.smtp_port, context=context) as server:
            server.ehlo()
            print("Support:", server.esmtp_features)
            server.login(email_setting.username, email_setting.password)
            server.send_message(msg)

    def main(self, title: str, body: str, attach_file: str = None):
        self.send_mail(self.create_message_body(title, body, attach_file))


if __name__ == "__main__":
    if not ((len(sys.argv) == 3) or (len(sys.argv) == 4)):
        print("Usage: python notification.py <title> <message> <(option)attach_file>")
        sys.exit(1)

    title = sys.argv[1]
    message = sys.argv[2]
    if len(sys.argv) == 4:
        attach_file = sys.argv[3]
    else:
        attach_file = None

    mailer = Mailer()
    mailer.main(title, message, attach_file)
