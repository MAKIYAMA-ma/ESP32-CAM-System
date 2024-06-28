from email.message import EmailMessage
import email_setting
import smtplib
import sys
import ssl


def create_message_body(title: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = title
    msg["From"] = email_setting.from_address
    msg["To"] = email_setting.to_address

    return msg


def send_mail(msg: EmailMessage):
    context = ssl.create_default_context()
    # with smtplib.SMTP(email_setting.smtp_host, email_setting.smtp_port) as server:
    with smtplib.SMTP_SSL(email_setting.smtp_host, email_setting.smtp_port, context=context) as server:
        server.ehlo()
        print("Support:", server.esmtp_features)
        server.login(email_setting.username, email_setting.password)
        server.send_message(msg)


def main(title: str, body: str):
    send_mail(create_message_body(title, body))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python notification.py <title> <message>")
        sys.exit(1)

    title = sys.argv[1]
    message = sys.argv[2]

    main(title, message)
