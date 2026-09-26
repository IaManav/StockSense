"""Transactional email delivery for account workflows."""

import os
import smtplib
import ssl
from email.message import EmailMessage


class EmailDeliveryError(RuntimeError):
    """Raised when an email cannot be handed to the configured SMTP server."""


def send_password_reset_email(recipient: str, code: str, expires_minutes: int = 10) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        raise EmailDeliveryError("Password reset email is not configured. Set SMTP_HOST and SMTP_FROM.")

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", username).strip()
    if not sender:
        raise EmailDeliveryError("Password reset email is not configured. Set SMTP_FROM.")

    message = EmailMessage()
    message["Subject"] = "StockSense password reset code"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Your StockSense password reset code is: {code}\n\n"
        f"This code expires in {expires_minutes} minutes. If you did not request this, you can ignore this email."
    )

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            if os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}:
                server.starttls(context=context)
                server.ehlo()
            if username:
                server.login(username, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError("Unable to send the password reset email. Try again later.") from exc
