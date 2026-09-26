from datetime import datetime

from extensions import db
from models.delivery import Delivery
from models.delivery_item import DeliveryItem
from stock_service import decrease_stock
from ledger_service import create_ledger_entry


def list_deliveries(status=None, warehouse_id=None):
    query = Delivery.query

    if status:
        query = query.filter_by(status=status)

    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)

    return query.order_by(Delivery.created_at.desc()).all()


def get_delivery(delivery_id):
    return db.session.get(Delivery, delivery_id)


def create_delivery(data, responsible_id):
    reference = data.get("reference")

    if not reference:
        raise ValueError("reference is required")

    if Delivery.query.filter_by(reference=reference).first():
        raise ValueError("Delivery reference already exists")

    delivery = Delivery(
        reference=reference,
        warehouse_id=data["warehouse_id"],
        delivery_address=data["delivery_address"],
        schedule_date=data["schedule_date"],
        operation_type=data.get("operation_type"),
        status="DRAFT",
        responsible_id=responsible_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(delivery)
    db.session.commit()
    return delivery


def update_delivery(delivery_id, data):
    delivery = get_delivery(delivery_id)

    if not delivery:
        raise ValueError("Delivery not found")

    if delivery.status != "DRAFT":
        raise ValueError("Only DRAFT deliveries can be edited")

    for field in (
        "warehouse_id",
        "delivery_address",
        "schedule_date",
        "operation_type",
    ):
        if field in data:
            setattr(delivery, field, data[field])

    delivery.updated_at = datetime.utcnow()
    db.session.commit()
    return delivery


def add_item(delivery_id, data):
    delivery = get_delivery(delivery_id)

    if not delivery or delivery.status != "DRAFT":
        raise ValueError("Delivery not found or not editable")

    if data.get("quantity") is None or float(data["quantity"]) <= 0:
        raise ValueError("quantity must be greater than zero")

    item = DeliveryItem(
        delivery_id=delivery_id,
        product_id=data["product_id"],
        location_id=data["location_id"],
        quantity=data["quantity"],
    )

    db.session.add(item)
    db.session.commit()
    return item


def update_item(delivery_id, item_id, data):
    delivery = get_delivery(delivery_id)

    if not delivery or delivery.status != "DRAFT":
        raise ValueError("Delivery not found or not editable")

    item = db.session.get(DeliveryItem, item_id)

    if not item or item.delivery_id != delivery.id:
        raise ValueError("Delivery item not found")

    for field in ("product_id", "location_id", "quantity"):
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return item


def delete_item(delivery_id, item_id):
    delivery = get_delivery(delivery_id)

    if not delivery or delivery.status != "DRAFT":
        raise ValueError("Delivery not found or not editable")

    item = db.session.get(DeliveryItem, item_id)

    if not item or item.delivery_id != delivery.id:
        raise ValueError("Delivery item not found")

    db.session.delete(item)
    db.session.commit()


def mark_ready(delivery_id):
    delivery = get_delivery(delivery_id)

    if not delivery:
        raise ValueError("Delivery not found")

    if delivery.status != "DRAFT":
        raise ValueError("Only DRAFT deliveries can become READY")

    if not delivery.items:
        raise ValueError("Delivery must contain at least one item")

    delivery.status = "READY"
    delivery.updated_at = datetime.utcnow()
    db.session.commit()
    return delivery


def validate_delivery(delivery_id, created_by):
    delivery = get_delivery(delivery_id)

    if not delivery:
        raise ValueError("Delivery not found")

    if delivery.status != "READY":
        raise ValueError("Only READY deliveries can be validated")

    try:
        for item in delivery.items:
            decrease_stock(
                item.product_id,
                item.location_id,
                item.quantity,
            )

            create_ledger_entry(
                reference=delivery.reference,
                product_id=item.product_id,
                from_location_id=item.location_id,
                to_location_id=None,
                quantity=item.quantity,
                move_type="OUT",
                source_type="DELIVERY",
                source_id=delivery.id,
                created_by=created_by,
                commit=False,
            )

        delivery.status = "DONE"
        delivery.updated_at = datetime.utcnow()
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return delivery


def cancel_delivery(delivery_id):
    delivery = get_delivery(delivery_id)

    if not delivery:
        raise ValueError("Delivery not found")

    if delivery.status == "DONE":
        raise ValueError("Completed delivery cannot be cancelled")

    delivery.status = "CANCELLED"
    delivery.updated_at = datetime.utcnow()
    db.session.commit()
    return delivery
