# student/services/email_service.py
import smtplib
from email.message import EmailMessage
from config import Config

def send_email(subject: str, body: str, to_email: str) -> bool:
    """
    Simple SMTP sender using MAIL_* env variables from Config.
    Returns True on success, False on failure (prints error).
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME or "noreply@example.com"
    msg["To"] = to_email
    msg.set_content(body)

    # If no mail server configured, print to console (dev mode)
    if not Config.MAIL_SERVER:
        print("[DEV EMAIL] No SMTP configured. Would send:")
        print("To:", to_email)
        print("Subject:", subject)
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
        # In production log this properly; for now print
        print("Error sending email:", e)
        return False
