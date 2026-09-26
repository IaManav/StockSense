from datetime import datetime
from decimal import Decimal

from extensions import db
from models.stock_adjustment import StockAdjustment
from models.adjustment_item import AdjustmentItem
from stock_service import get_or_create_stock
from ledger_service import create_ledger_entry


def list_adjustments(status=None, warehouse_id=None, location_id=None):
    query = StockAdjustment.query

    if status:
        query = query.filter_by(status=status)

    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)

    if location_id:
        query = query.filter_by(location_id=location_id)

    return query.order_by(StockAdjustment.created_at.desc()).all()


def get_adjustment(adjustment_id):
    return db.session.get(StockAdjustment, adjustment_id)


def create_adjustment(data, responsible_id):
    reference = data.get("reference")

    if not reference:
        raise ValueError("reference is required")

    if StockAdjustment.query.filter_by(reference=reference).first():
        raise ValueError("Adjustment reference already exists")

    adjustment = StockAdjustment(
        reference=reference,
        warehouse_id=data["warehouse_id"],
        location_id=data["location_id"],
        reason=data["reason"],
        status="DRAFT",
        responsible_id=responsible_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.session.add(adjustment)
    db.session.commit()
    return adjustment


def update_adjustment(adjustment_id, data):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment:
        raise ValueError("Adjustment not found")

    if adjustment.status != "DRAFT":
        raise ValueError("Only DRAFT adjustments can be edited")

    for field in ("warehouse_id", "location_id", "reason"):
        if field in data:
            setattr(adjustment, field, data[field])

    adjustment.updated_at = datetime.utcnow()
    db.session.commit()
    return adjustment


def add_item(adjustment_id, data):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment or adjustment.status != "DRAFT":
        raise ValueError("Adjustment not found or not editable")

    product_id = data["product_id"]
    counted_quantity = Decimal(str(data["counted_quantity"]))

    if counted_quantity < 0:
        raise ValueError("counted_quantity cannot be negative")

    stock = get_or_create_stock(
        product_id,
        adjustment.location_id,
    )

    old_quantity = stock.on_hand_quantity
    difference = counted_quantity - old_quantity

    item = AdjustmentItem(
        adjustment_id=adjustment_id,
        product_id=product_id,
        old_quantity=old_quantity,
        counted_quantity=counted_quantity,
        difference=difference,
    )

    db.session.add(item)
    db.session.commit()
    return item


def update_item(adjustment_id, item_id, data):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment or adjustment.status != "DRAFT":
        raise ValueError("Adjustment not found or not editable")

    item = db.session.get(AdjustmentItem, item_id)

    if not item or item.adjustment_id != adjustment.id:
        raise ValueError("Adjustment item not found")

    if "counted_quantity" in data:
        counted = Decimal(str(data["counted_quantity"]))

        if counted < 0:
            raise ValueError("counted_quantity cannot be negative")

        item.counted_quantity = counted
        item.difference = counted - item.old_quantity

    db.session.commit()
    return item


def delete_item(adjustment_id, item_id):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment or adjustment.status != "DRAFT":
        raise ValueError("Adjustment not found or not editable")

    item = db.session.get(AdjustmentItem, item_id)

    if not item or item.adjustment_id != adjustment.id:
        raise ValueError("Adjustment item not found")

    db.session.delete(item)
    db.session.commit()


def validate_adjustment(adjustment_id, created_by):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment:
        raise ValueError("Adjustment not found")

    if adjustment.status != "DRAFT":
        raise ValueError("Only DRAFT adjustments can be validated")

    if not adjustment.items:
        raise ValueError("Adjustment must contain at least one item")

    try:
        for item in adjustment.items:
            stock = get_or_create_stock(
                item.product_id,
                adjustment.location_id,
            )

            # Re-read the actual quantity at validation time.
            old_quantity = stock.on_hand_quantity
            new_quantity = item.counted_quantity
            difference = new_quantity - old_quantity

            stock.on_hand_quantity = new_quantity

            item.old_quantity = old_quantity
            item.difference = difference

            create_ledger_entry(
                reference=adjustment.reference,
                product_id=item.product_id,
                from_location_id=adjustment.location_id if difference < 0 else None,
                to_location_id=adjustment.location_id if difference > 0 else None,
                quantity=abs(difference),
                move_type="ADJUSTMENT",
                source_type="ADJUSTMENT",
                source_id=adjustment.id,
                created_by=created_by,
                commit=False,
            )

        adjustment.status = "DONE"
        adjustment.updated_at = datetime.utcnow()
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return adjustment


def cancel_adjustment(adjustment_id):
    adjustment = get_adjustment(adjustment_id)

    if not adjustment:
        raise ValueError("Adjustment not found")

    if adjustment.status == "DONE":
        raise ValueError("Completed adjustment cannot be cancelled")

    adjustment.status = "CANCELLED"
    adjustment.updated_at = datetime.utcnow()
    db.session.commit()
    return adjustment
