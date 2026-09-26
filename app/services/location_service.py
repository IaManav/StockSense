from sqlalchemy import select

from app.models import Location, Warehouse
from app.services.inventory_service import require


def list_locations(db, warehouse_id=None):
    query = select(Location).order_by(Location.name)
    if warehouse_id:
        query = query.where(Location.warehouse_id == warehouse_id)
    return db.scalars(query).all()


def create_location(db, data):
    require(db, Warehouse, data["warehouse_id"], "Warehouse")
    location = Location(warehouse_id=data["warehouse_id"], name=data["name"], short_code=data["short_code"].upper())
    db.add(location)
    db.commit()
    return location
