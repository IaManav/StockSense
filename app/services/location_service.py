from datetime import datetime

from extensions import db
from models.location import Location
from models.warehouse import Warehouse


def list_locations(warehouse_id=None):
    query = Location.query

    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)

    return query.order_by(Location.name.asc()).all()


def get_location(location_id):
    return db.session.get(Location, location_id)


def create_location(data):
    warehouse_id = data.get("warehouse_id")
    name = data.get("name")
    short_code = data.get("short_code")

    if not warehouse_id or not name or not short_code:
        raise ValueError("warehouse_id, name and short_code are required")

    if not db.session.get(Warehouse, warehouse_id):
        raise ValueError("Warehouse not found")

    existing = Location.query.filter_by(
        warehouse_id=warehouse_id,
        short_code=short_code,
    ).first()

    if existing:
        raise ValueError("Location short_code already exists in this warehouse")

    location = Location(
        warehouse_id=warehouse_id,
        name=name,
        short_code=short_code,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(location)
    db.session.commit()
    return location


def update_location(location_id, data):
    location = get_location(location_id)
    if not location:
        raise ValueError("Location not found")

    if "warehouse_id" in data:
        if not db.session.get(Warehouse, data["warehouse_id"]):
            raise ValueError("Warehouse not found")
        location.warehouse_id = data["warehouse_id"]

    if "short_code" in data:
        existing = Location.query.filter(
            Location.warehouse_id == location.warehouse_id,
            Location.short_code == data["short_code"],
            Location.id != location.id,
        ).first()
        if existing:
            raise ValueError("Location short_code already exists in this warehouse")

    for field in ("name", "short_code"):
        if field in data:
            setattr(location, field, data[field])

    location.updated_at = datetime.utcnow()
    db.session.commit()
    return location


def delete_location(location_id):
    location = get_location(location_id)
    if not location:
        raise ValueError("Location not found")

    db.session.delete(location)
    db.session.commit()
    return location
