"""Transactional email. If MAIL_SERVER isn't configured (typical in local
development) the message is printed to the backend console instead, so
verification and password-reset links are still usable while developing."""
import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email(to, subject, body):
    cfg = current_app.config
    if not cfg["MAIL_SERVER"]:
        print(f"\n[dev mail] To: {to}\n[dev mail] Subject: {subject}\n[dev mail] {body}\n", flush=True)
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg["MAIL_DEFAULT_SENDER"], to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"], timeout=10) as smtp:
            smtp.starttls()
            if cfg["MAIL_USERNAME"]:
                smtp.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            smtp.send_message(msg)
        return True
    except Exception as exc:  # never crash a request because mail failed
        current_app.logger.error("Email send failed: %s", type(exc).__name__)
        return False
