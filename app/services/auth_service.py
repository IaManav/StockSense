from datetime import datetime, timedelta
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models.user import User


def signup(login_id, email, password):
    if not login_id or not email or not password:
        raise ValueError("login_id, email and password are required")

    if not 6 <= len(login_id) <= 12:
        raise ValueError("login_id must be 6-12 characters")

    if User.query.filter_by(login_id=login_id).first():
        raise ValueError("login_id already exists")

    if User.query.filter_by(email=email).first():
        raise ValueError("email already exists")

    user = User(
        login_id=login_id,
        email=email,
        password_hash=generate_password_hash(password),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(login_id, password):
    user = User.query.filter_by(login_id=login_id).first()

    if not user or not check_password_hash(user.password_hash, password):
        return None

    return user


def generate_reset_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def request_password_reset(email):
    user = User.query.filter_by(email=email).first()

    # Do not expose whether an email exists at the API layer.
    if not user:
        return None

    otp = generate_reset_otp()

    # TODO: Persist OTP in a dedicated PasswordReset/OTP table
    # and send it through your email/SMS provider.
    return {
        "user_id": str(user.id),
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }


def reset_password(user, new_password):
    if not new_password:
        raise ValueError("new_password is required")

    user.password_hash = generate_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return user
