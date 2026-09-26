from datetime import datetime

from extensions import db
from models.stock_ledger import StockLedger


def create_ledger_entry(
    reference,
    product_id,
    from_location_id,
    to_location_id,
    quantity,
    move_type,
    source_type,
    source_id,
    created_by,
    commit=True,
):
    entry = StockLedger(
        reference=reference,
        product_id=product_id,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        quantity=quantity,
        move_type=move_type,
        source_type=source_type,
        source_id=source_id,
        created_by=created_by,
        created_at=datetime.utcnow(),
    )

    db.session.add(entry)

    if commit:
        db.session.commit()

    return entry


def list_ledger(
    product_id=None,
    location_id=None,
    move_type=None,
    source_type=None,
    from_date=None,
    to_date=None,
):
    query = StockLedger.query

    if product_id:
        query = query.filter_by(product_id=product_id)

    if location_id:
        query = query.filter(
            db.or_(
                StockLedger.from_location_id == location_id,
                StockLedger.to_location_id == location_id,
            )
        )

    if move_type:
        query = query.filter_by(move_type=move_type)

    if source_type:
        query = query.filter_by(source_type=source_type)

    if from_date:
        query = query.filter(StockLedger.created_at >= from_date)

    if to_date:
        query = query.filter(StockLedger.created_at <= to_date)

    return query.order_by(StockLedger.created_at.desc()).all()


def get_ledger_entry(ledger_id):
    return db.session.get(StockLedger, ledger_id)


def get_product_ledger(product_id):
    return list_ledger(product_id=product_id)


def get_location_ledger(location_id):
    return list_ledger(location_id=location_id)
