from flask import g
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import database_url as get_database_url


DATABASE_URL = get_database_url()


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    if "db" not in g:
        g.db = SessionLocal()

    return g.db


def init_app(app) -> None:
    """Register database cleanup with the Flask application."""
    app.teardown_appcontext(close_db)


def close_db(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()
