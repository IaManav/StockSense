from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User
from app.services.inventory_service import require


def get_user(db: Session, user_id):
    return require(db, User, user_id, "User")


def update_profile(db: Session, user_id, data: dict) -> User:
    user = get_user(db, user_id)
    for field in ("login_id", "email"):
        if field in data:
            setattr(user, field, data[field].strip().lower() if field == "email" else data[field].strip())
    db.commit()
    return user


def change_password(db: Session, user_id, old_password: str, new_password: str) -> User:
    user = get_user(db, user_id)
    if not check_password_hash(user.password_hash, old_password):
        raise ValueError("Current password is incorrect")
    user.password_hash = generate_password_hash(new_password)
    db.commit()
    return user
