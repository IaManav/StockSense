"""Reusable validation rules for user-facing input."""

import re


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(value: str) -> str:
    email = str(value or "").strip().lower()
    if len(email) > 255 or not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Enter a valid email address")
    return email


def validate_password(value: str) -> str:
    password = str(value or "")
    missing = []
    if len(password) < 8:
        missing.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        missing.append("one uppercase letter")
    if not re.search(r"\d", password):
        missing.append("one number")
    if not re.search(r"[^A-Za-z0-9]", password):
        missing.append("one special character")
    if missing:
        raise ValueError("Password must contain " + ", ".join(missing))
    return password
