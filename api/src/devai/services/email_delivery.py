"""Authenticated TLS SMTP delivery; no console-mail fallback or exposed codes."""

import os
import smtplib
import ssl
from email.message import EmailMessage


def mail_configured():
    return bool(
        os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM") and len(os.getenv("APP_SECRET", "")) >= 32
    )


def deliver_code(email, code):
    if not mail_configured():
        raise RuntimeError("Email authentication is not configured")
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = email
    message["Subject"] = "Your DevAI Studio sign-in code"
    message.set_content(
        f"Your DevAI Studio code is {code}.\n\nIt expires in 10 minutes. If you did not request it, ignore this email. Never share this code."
    )
    host = os.environ["SMTP_HOST"]
    use_ssl = os.getenv("SMTP_TLS_MODE", "starttls") == "ssl"
    port = int(os.getenv("SMTP_PORT", "465" if use_ssl else "587"))
    context = ssl.create_default_context()
    connection = (
        smtplib.SMTP_SSL(host, port, timeout=15, context=context)
        if use_ssl
        else smtplib.SMTP(host, port, timeout=15)
    )
    with connection as smtp:
        if not use_ssl:
            smtp.starttls(context=context)
        username = os.getenv("SMTP_USERNAME")
        if username:
            smtp.login(username, os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)
