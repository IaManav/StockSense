from datetime import datetime
from decimal import Decimal

from extensions import db
from models.product import Product
from models.category import Category


def list_products(search=None, category_id=None, is_active=None):
    query = Product.query

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if is_active is not None:
        query = query.filter_by(is_active=is_active)

    return query.order_by(Product.name.asc()).all()


def get_product(product_id):
    return db.session.get(Product, product_id)


def create_product(data):
    required = ("sku", "name", "category_id", "unit_of_measure", "unit_cost", "reorder_level")

    for field in required:
        if data.get(field) is None:
            raise ValueError(f"{field} is required")

    if Product.query.filter_by(sku=data["sku"]).first():
        raise ValueError("SKU already exists")

    if not db.session.get(Category, data["category_id"]):
        raise ValueError("Category not found")

    product = Product(
        sku=data["sku"],
        name=data["name"],
        category_id=data["category_id"],
        unit_of_measure=data["unit_of_measure"],
        unit_cost=Decimal(str(data["unit_cost"])),
        reorder_level=Decimal(str(data["reorder_level"])),
        is_active=data.get("is_active", True),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(product)
    db.session.commit()

    # Initial stock, when supplied, should be handled through a stock/ledger
    # transaction rather than directly changing Product.
    return product


def update_product(product_id, data):
    product = get_product(product_id)
    if not product:
        raise ValueError("Product not found")

    if "sku" in data:
        existing = Product.query.filter(
            Product.sku == data["sku"],
            Product.id != product.id,
        ).first()
        if existing:
            raise ValueError("SKU already exists")
        product.sku = data["sku"]

    if "category_id" in data:
        if not db.session.get(Category, data["category_id"]):
            raise ValueError("Category not found")
        product.category_id = data["category_id"]

    for field in ("name", "unit_of_measure", "is_active"):
        if field in data:
            setattr(product, field, data[field])

    if "unit_cost" in data:
        product.unit_cost = Decimal(str(data["unit_cost"]))

    if "reorder_level" in data:
        product.reorder_level = Decimal(str(data["reorder_level"]))

    product.updated_at = datetime.utcnow()
    db.session.commit()
    return product


def deactivate_product(product_id):
    product = get_product(product_id)
    if not product:
        raise ValueError("Product not found")

    product.is_active = False
    product.updated_at = datetime.utcnow()
    db.session.commit()
    return product
