from extensions import db
from models.category import Category


def list_categories():
    return Category.query.order_by(Category.name.asc()).all()


def get_category(category_id):
    return db.session.get(Category, category_id)


def create_category(data):
    name = data.get("name")
    description = data.get("description")

    if not name:
        raise ValueError("name is required")

    if Category.query.filter_by(name=name).first():
        raise ValueError("Category already exists")

    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    if not category:
        raise ValueError("Category not found")

    if "name" in data:
        existing = Category.query.filter(
            Category.name == data["name"],
            Category.id != category.id,
        ).first()
        if existing:
            raise ValueError("Category already exists")
        category.name = data["name"]

    if "description" in data:
        category.description = data["description"]

    db.session.commit()
    return category


def delete_category(category_id):
    category = get_category(category_id)
    if not category:
        raise ValueError("Category not found")

    db.session.delete(category)
    db.session.commit()
    return category
