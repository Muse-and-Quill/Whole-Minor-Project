# Faculty/services/email_service.py
import smtplib
from email.message import EmailMessage
from config import Config

def send_email(subject: str, body: str, to_email: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME or "noreply@example.com"
    msg["To"] = to_email
    msg.set_content(body)

    if not Config.MAIL_SERVER:
        print("[DEV EMAIL] Would send:", subject, "to", to_email)
        print(body)
        return True

    try:
        if Config.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                server.ehlo()
                if Config.MAIL_USE_TLS:
                    server.starttls()
                if Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
                    server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.send_message(msg)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False
