from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Stock
from app.services.inventory_service import change_stock, get_or_create_stock


def get_stock(db: Session, product_id=None, location_id=None):
    query = select(Stock)
    if product_id:
        query = query.where(Stock.product_id == product_id)
    if location_id:
        query = query.where(Stock.location_id == location_id)
    return db.scalars(query).all()


def increase_stock(db: Session, product_id, location_id, quantity):
    return change_stock(db, product_id, location_id, quantity, 1)


def decrease_stock(db: Session, product_id, location_id, quantity):
    return change_stock(db, product_id, location_id, quantity, -1)


__all__ = ["get_or_create_stock", "get_stock", "increase_stock", "decrease_stock"]
