from datetime import datetime

from extensions import db
from models.user import User


def get_user(user_id):
    return db.session.get(User, user_id)


def update_profile(user_id, data):
    user = get_user(user_id)
    if not user:
        raise ValueError("User not found")

    if "login_id" in data:
        existing = User.query.filter(
            User.login_id == data["login_id"],
            User.id != user.id,
        ).first()
        if existing:
            raise ValueError("login_id already exists")
        user.login_id = data["login_id"]

    if "email" in data:
        existing = User.query.filter(
            User.email == data["email"],
            User.id != user.id,
        ).first()
        if existing:
            raise ValueError("email already exists")
        user.email = data["email"]

    user.updated_at = datetime.utcnow()
    db.session.commit()
    return user


def change_password(user_id, old_password, new_password):
    from werkzeug.security import check_password_hash, generate_password_hash

    user = get_user(user_id)
    if not user:
        raise ValueError("User not found")

    if not check_password_hash(user.password_hash, old_password):
        raise ValueError("Current password is incorrect")

    user.password_hash = generate_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    return user
