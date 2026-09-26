from sqlalchemy import func

from extensions import db
from models.product import Product
from models.stock import Stock
from models.receipt import Receipt
from models.delivery import Delivery
from models.stock_transfer import StockTransfer


def get_summary():
    total_products = (
        db.session.query(func.count(func.distinct(Stock.product_id)))
        .filter(
            (Stock.on_hand_quantity - Stock.reserved_quantity) > 0
        )
        .scalar()
        or 0
    )

    low_stock_items = (
        db.session.query(func.count(func.distinct(Stock.product_id)))
        .join(Product, Product.id == Stock.product_id)
        .filter(
            (Stock.on_hand_quantity - Stock.reserved_quantity)
            <= Product.reorder_level,
            (Stock.on_hand_quantity - Stock.reserved_quantity) > 0,
        )
        .scalar()
        or 0
    )

    out_of_stock_items = (
        db.session.query(func.count(func.distinct(Stock.product_id)))
        .filter(
            (Stock.on_hand_quantity - Stock.reserved_quantity) <= 0
        )
        .scalar()
        or 0
    )

    pending_receipts = (
        Receipt.query
        .filter(Receipt.status.in_(["DRAFT", "READY"]))
        .count()
    )

    pending_deliveries = (
        Delivery.query
        .filter(Delivery.status.in_(["DRAFT", "WAITING", "READY"]))
        .count()
    )

    scheduled_transfers = (
        StockTransfer.query
        .filter(StockTransfer.status.in_(["DRAFT", "READY"]))
        .count()
    )

    return {
        "total_products": total_products,
        "low_stock_items": low_stock_items,
        "out_of_stock_items": out_of_stock_items,
        "pending_receipts": pending_receipts,
        "pending_deliveries": pending_deliveries,
        "scheduled_transfers": scheduled_transfers,
    }


def get_stock_dashboard(warehouse_id=None, location_id=None, category_id=None):
    # This intentionally returns raw Stock rows. The route/schema layer
    # can serialize them into the dashboard format.
    from models.location import Location

    query = (
        Stock.query
        .join(Product, Product.id == Stock.product_id)
        .join(Location, Location.id == Stock.location_id)
    )

    if warehouse_id:
        query = query.filter(Location.warehouse_id == warehouse_id)

    if location_id:
        query = query.filter(Stock.location_id == location_id)

    if category_id:
        query = query.filter(Product.category_id == category_id)

    return query.all()


def get_operations_dashboard(
    document_type=None,
    status=None,
    warehouse_id=None,
):
    results = []

    if document_type in (None, "receipts"):
        query = Receipt.query
        if status:
            query = query.filter_by(status=status)
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)

        results.extend(("receipt", x) for x in query.all())

    if document_type in (None, "deliveries"):
        query = Delivery.query
        if status:
            query = query.filter_by(status=status)
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)

        results.extend(("delivery", x) for x in query.all())

    if document_type in (None, "transfers"):
        query = StockTransfer.query
        if status:
            query = query.filter_by(status=status)

        results.extend(("transfer", x) for x in query.all())

    if document_type in (None, "adjustments"):
        from models.stock_adjustment import StockAdjustment

        query = StockAdjustment.query
        if status:
            query = query.filter_by(status=status)
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)

        results.extend(("adjustment", x) for x in query.all())

    return results
