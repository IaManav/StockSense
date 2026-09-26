from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User
from app.validation import validate_email, validate_password


def signup(db: Session, login_id: str, email: str, password: str) -> User:
    login_id, email = login_id.strip(), validate_email(email)
    validate_password(password)
    if not 6 <= len(login_id) <= 12:
        raise ValueError("login_id must be 6-12 characters")
    if db.scalar(select(User).where((User.login_id == login_id) | (User.email == email))):
        raise ValueError("login_id or email already exists")
    user = User(login_id=login_id, email=email, password_hash=generate_password_hash(password))
    db.add(user)
    db.commit()
    return user


def authenticate(db: Session, login_id: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.login_id == login_id.strip()))
    return user if user and check_password_hash(user.password_hash, password) else None
