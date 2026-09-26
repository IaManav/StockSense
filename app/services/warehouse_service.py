from sqlalchemy import select

from app.models import Warehouse
from app.services.inventory_service import require


def list_warehouses(db):
    return db.scalars(select(Warehouse).order_by(Warehouse.name)).all()


def get_warehouse(db, warehouse_id):
    return require(db, Warehouse, warehouse_id, "Warehouse")


def create_warehouse(db, data):
    warehouse = Warehouse(name=data["name"], short_code=data["short_code"].upper(), address=data.get("address"))
    db.add(warehouse)
    db.commit()
    return warehouse
