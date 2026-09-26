from datetime import datetime

from extensions import db
from models.stock_transfer import StockTransfer
from models.transfer_item import TransferItem
from stock_service import transfer_stock
from ledger_service import create_ledger_entry


def list_transfers(status=None, from_location_id=None, to_location_id=None):
    query = StockTransfer.query

    if status:
        query = query.filter_by(status=status)

    if from_location_id:
        query = query.filter_by(from_location_id=from_location_id)

    if to_location_id:
        query = query.filter_by(to_location_id=to_location_id)

    return query.order_by(StockTransfer.created_at.desc()).all()


def get_transfer(transfer_id):
    return db.session.get(StockTransfer, transfer_id)


def create_transfer(data, responsible_id):
    reference = data.get("reference")

    if not reference:
        raise ValueError("reference is required")

    if data["from_location_id"] == data["to_location_id"]:
        raise ValueError("Source and destination locations must be different")

    if StockTransfer.query.filter_by(reference=reference).first():
        raise ValueError("Transfer reference already exists")

    transfer = StockTransfer(
        reference=reference,
        from_location_id=data["from_location_id"],
        to_location_id=data["to_location_id"],
        status="DRAFT",
        responsible_id=responsible_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(transfer)
    db.session.commit()
    return transfer


def update_transfer(transfer_id, data):
    transfer = get_transfer(transfer_id)

    if not transfer:
        raise ValueError("Transfer not found")

    if transfer.status != "DRAFT":
        raise ValueError("Only DRAFT transfers can be edited")

    from_location = data.get("from_location_id", transfer.from_location_id)
    to_location = data.get("to_location_id", transfer.to_location_id)

    if from_location == to_location:
        raise ValueError("Source and destination locations must be different")

    transfer.from_location_id = from_location
    transfer.to_location_id = to_location
    transfer.updated_at = datetime.utcnow()

    db.session.commit()
    return transfer


def add_item(transfer_id, data):
    transfer = get_transfer(transfer_id)

    if not transfer or transfer.status != "DRAFT":
        raise ValueError("Transfer not found or not editable")

    if data.get("quantity") is None or float(data["quantity"]) <= 0:
        raise ValueError("quantity must be greater than zero")

    item = TransferItem(
        transfer_id=transfer_id,
        product_id=data["product_id"],
        quantity=data["quantity"],
    )

    db.session.add(item)
    db.session.commit()
    return item


def update_item(transfer_id, item_id, data):
    transfer = get_transfer(transfer_id)

    if not transfer or transfer.status != "DRAFT":
        raise ValueError("Transfer not found or not editable")

    item = db.session.get(TransferItem, item_id)

    if not item or item.transfer_id != transfer.id:
        raise ValueError("Transfer item not found")

    for field in ("product_id", "quantity"):
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return item


def delete_item(transfer_id, item_id):
    transfer = get_transfer(transfer_id)

    if not transfer or transfer.status != "DRAFT":
        raise ValueError("Transfer not found or not editable")

    item = db.session.get(TransferItem, item_id)

    if not item or item.transfer_id != transfer.id:
        raise ValueError("Transfer item not found")

    db.session.delete(item)
    db.session.commit()


def mark_ready(transfer_id):
    transfer = get_transfer(transfer_id)

    if not transfer:
        raise ValueError("Transfer not found")

    if transfer.status != "DRAFT":
        raise ValueError("Only DRAFT transfers can become READY")

    if not transfer.items:
        raise ValueError("Transfer must contain at least one item")

    transfer.status = "READY"
    transfer.updated_at = datetime.utcnow()
    db.session.commit()
    return transfer


def validate_transfer(transfer_id, created_by):
    transfer = get_transfer(transfer_id)

    if not transfer:
        raise ValueError("Transfer not found")

    if transfer.status != "READY":
        raise ValueError("Only READY transfers can be validated")

    try:
        for item in transfer.items:
            transfer_stock(
                item.product_id,
                transfer.from_location_id,
                transfer.to_location_id,
                item.quantity,
            )

            create_ledger_entry(
                reference=transfer.reference,
                product_id=item.product_id,
                from_location_id=transfer.from_location_id,
                to_location_id=transfer.to_location_id,
                quantity=item.quantity,
                move_type="TRANSFER",
                source_type="TRANSFER",
                source_id=transfer.id,
                created_by=created_by,
                commit=False,
            )

        transfer.status = "DONE"
        transfer.updated_at = datetime.utcnow()
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return transfer


def cancel_transfer(transfer_id):
    transfer = get_transfer(transfer_id)

    if not transfer:
        raise ValueError("Transfer not found")

    if transfer.status == "DONE":
        raise ValueError("Completed transfer cannot be cancelled")

    transfer.status = "CANCELLED"
    transfer.updated_at = datetime.utcnow()
    db.session.commit()
    return transfer
