from sqlalchemy import select

from app.models import StockMove


def list_ledger(db, product_id=None, location_id=None):
    query = select(StockMove).order_by(StockMove.id.desc())
    if product_id:
        query = query.where(StockMove.product_id == product_id)
    if location_id:
        query = query.where((StockMove.from_location_id == location_id) | (StockMove.to_location_id == location_id))
    return db.scalars(query).all()
