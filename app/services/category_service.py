from sqlalchemy import select

from app.models import Category
from app.services.inventory_service import require


def list_categories(db):
    return db.scalars(select(Category).order_by(Category.name)).all()


def get_category(db, category_id):
    return require(db, Category, category_id, "Category")


def create_category(db, data):
    category = Category(name=data["name"], description=data.get("description"))
    db.add(category)
    db.commit()
    return category
