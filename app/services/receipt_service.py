from datetime import datetime

from extensions import db
from models.receipt import Receipt
from models.receipt_item import ReceiptItem
from stock_service import increase_stock
from ledger_service import create_ledger_entry


def list_receipts(status=None, warehouse_id=None):
    query = Receipt.query

    if status:
        query = query.filter_by(status=status)

    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)

    return query.order_by(Receipt.created_at.desc()).all()


def get_receipt(receipt_id):
    return db.session.get(Receipt, receipt_id)


def create_receipt(data, responsible_id):
    reference = data.get("reference")

    if not reference:
        raise ValueError("reference is required")

    if Receipt.query.filter_by(reference=reference).first():
        raise ValueError("Receipt reference already exists")

    receipt = Receipt(
        reference=reference,
        warehouse_id=data["warehouse_id"],
        receive_from=data["receive_from"],
        schedule_date=data["schedule_date"],
        status="DRAFT",
        responsible_id=responsible_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(receipt)
    db.session.commit()
    return receipt


def update_receipt(receipt_id, data):
    receipt = get_receipt(receipt_id)
    if not receipt:
        raise ValueError("Receipt not found")

    if receipt.status != "DRAFT":
        raise ValueError("Only DRAFT receipts can be edited")

    for field in ("warehouse_id", "receive_from", "schedule_date"):
        if field in data:
            setattr(receipt, field, data[field])

    receipt.updated_at = datetime.utcnow()
    db.session.commit()
    return receipt


def add_item(receipt_id, data):
    receipt = get_receipt(receipt_id)

    if not receipt:
        raise ValueError("Receipt not found")

    if receipt.status != "DRAFT":
        raise ValueError("Items can only be added to DRAFT receipts")

    quantity = data.get("quantity")
    if quantity is None or float(quantity) <= 0:
        raise ValueError("quantity must be greater than zero")

    item = ReceiptItem(
        receipt_id=receipt_id,
        product_id=data["product_id"],
        location_id=data["location_id"],
        quantity=quantity,
    )

    db.session.add(item)
    db.session.commit()
    return item


def update_item(receipt_id, item_id, data):
    receipt = get_receipt(receipt_id)

    if not receipt or receipt.status != "DRAFT":
        raise ValueError("Receipt not found or not editable")

    item = db.session.get(ReceiptItem, item_id)
    if not item or item.receipt_id != receipt.id:
        raise ValueError("Receipt item not found")

    if "quantity" in data:
        item.quantity = data["quantity"]
    if "product_id" in data:
        item.product_id = data["product_id"]
    if "location_id" in data:
        item.location_id = data["location_id"]

    db.session.commit()
    return item


def delete_item(receipt_id, item_id):
    receipt = get_receipt(receipt_id)

    if not receipt or receipt.status != "DRAFT":
        raise ValueError("Receipt not found or not editable")

    item = db.session.get(ReceiptItem, item_id)
    if not item or item.receipt_id != receipt.id:
        raise ValueError("Receipt item not found")

    db.session.delete(item)
    db.session.commit()


def mark_ready(receipt_id):
    receipt = get_receipt(receipt_id)

    if not receipt:
        raise ValueError("Receipt not found")

    if receipt.status != "DRAFT":
        raise ValueError("Only DRAFT receipts can become READY")

    if not receipt.items:
        raise ValueError("Receipt must contain at least one item")

    receipt.status = "READY"
    receipt.updated_at = datetime.utcnow()
    db.session.commit()
    return receipt


def validate_receipt(receipt_id, created_by):
    receipt = get_receipt(receipt_id)

    if not receipt:
        raise ValueError("Receipt not found")

    if receipt.status != "READY":
        raise ValueError("Only READY receipts can be validated")

    try:
        for item in receipt.items:
            increase_stock(
                item.product_id,
                item.location_id,
                item.quantity,
            )

            create_ledger_entry(
                reference=receipt.reference,
                product_id=item.product_id,
                from_location_id=None,
                to_location_id=item.location_id,
                quantity=item.quantity,
                move_type="IN",
                source_type="RECEIPT",
                source_id=receipt.id,
                created_by=created_by,
                commit=False,
            )

        receipt.status = "DONE"
        receipt.updated_at = datetime.utcnow()
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return receipt


def cancel_receipt(receipt_id):
    receipt = get_receipt(receipt_id)

    if not receipt:
        raise ValueError("Receipt not found")

    if receipt.status == "DONE":
        raise ValueError("Completed receipt cannot be cancelled")

    receipt.status = "CANCELLED"
    receipt.updated_at = datetime.utcnow()
    db.session.commit()
    return receipt
