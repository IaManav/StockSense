from datetime import datetime

from extensions import db
from models.warehouse import Warehouse


def list_warehouses():
    return Warehouse.query.order_by(Warehouse.name.asc()).all()


def get_warehouse(warehouse_id):
    return db.session.get(Warehouse, warehouse_id)


def create_warehouse(data):
    name = data.get("name")
    short_code = data.get("short_code")
    address = data.get("address")

    if not name or not short_code or not address:
        raise ValueError("name, short_code and address are required")

    if Warehouse.query.filter_by(short_code=short_code).first():
        raise ValueError("short_code already exists")

    warehouse = Warehouse(
        name=name,
        short_code=short_code,
        address=address,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(warehouse)
    db.session.commit()
    return warehouse


def update_warehouse(warehouse_id, data):
    warehouse = get_warehouse(warehouse_id)
    if not warehouse:
        raise ValueError("Warehouse not found")

    if "short_code" in data:
        existing = Warehouse.query.filter(
            Warehouse.short_code == data["short_code"],
            Warehouse.id != warehouse.id,
        ).first()
        if existing:
            raise ValueError("short_code already exists")

    for field in ("name", "short_code", "address"):
        if field in data:
            setattr(warehouse, field, data[field])

    warehouse.updated_at = datetime.utcnow()
    db.session.commit()
    return warehouse


def delete_warehouse(warehouse_id):
    warehouse = get_warehouse(warehouse_id)
    if not warehouse:
        raise ValueError("Warehouse not found")

    db.session.delete(warehouse)
    db.session.commit()
    return warehouse
