from sqlalchemy import select

from app.models import Product
from app.services.inventory_service import decimal_value, require


def list_products(db, search=None, category_id=None, is_active=None):
    query = select(Product).order_by(Product.name)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))
    if category_id:
        query = query.where(Product.category_id == category_id)
    if is_active is not None:
        query = query.where(Product.is_active == is_active)
    return db.scalars(query).all()


def get_product(db, product_id):
    return require(db, Product, product_id, "Product")


def create_product(db, data):
    product = Product(sku=data["sku"].upper(), name=data["name"], description=data.get("description"), category_id=data.get("category_id"), unit=data.get("unit", "piece"), unit_cost=decimal_value(data.get("unit_cost", 0), "unit_cost", allow_zero=True), reorder_level=decimal_value(data.get("reorder_level", 0), "reorder_level", allow_zero=True))
    db.add(product)
    db.commit()
    return product
