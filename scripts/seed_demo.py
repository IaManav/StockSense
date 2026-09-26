"""Insert a repeatable demo dataset into the configured PostgreSQL database."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.database import SessionLocal
from app.models import (
    Category,
    Delivery,
    DeliveryItem,
    Location,
    Product,
    Receipt,
    ReceiptItem,
    Stock,
    StockAdjustment,
    StockAdjustmentItem,
    StockMove,
    StockTransfer,
    TransferItem,
    User,
    Warehouse,
)
from app.models.adjustment import AdjustmentStatus
from app.models.delivery import DeliveryStatus
from app.models.receipt import ReceiptStatus
from app.models.stock_move import MoveType, SourceType
from app.models.transfer import TransferStatus
from app.models.user import UserRole


def one(session, model, **filters):
    return session.scalar(select(model).filter_by(**filters))


def seed_demo() -> None:
    with SessionLocal.begin() as session:
        user = one(session, User, login_id="demo01")
        if user is None:
            user = User(
                login_id="demo01",
                email="demo@stocksense.local",
                password_hash=generate_password_hash("Demo123!"),
                role=UserRole.ADMIN,
            )
            session.add(user)
            session.flush()

        warehouse = one(session, Warehouse, short_code="MAIN")
        if warehouse is None:
            warehouse = Warehouse(
                name="Main Warehouse", short_code="MAIN", address="12 Industrial Road"
            )
            session.add(warehouse)
            session.flush()

        locations = {}
        for name, code in (("Receiving", "RECV"), ("Rack A", "RACK-A"), ("Production Floor", "PROD")):
            location = one(session, Location, warehouse_id=warehouse.id, short_code=code)
            if location is None:
                location = Location(warehouse_id=warehouse.id, name=name, short_code=code)
                session.add(location)
                session.flush()
            locations[code] = location

        categories = {}
        for name, description in (("Raw materials", "Materials used in production"), ("Finished goods", "Ready for shipment")):
            category = one(session, Category, name=name)
            if category is None:
                category = Category(name=name, description=description)
                session.add(category)
                session.flush()
            categories[name] = category

        products = {}
        product_specs = (
            ("STEEL-ROD", "Steel Rod", "kg", "Raw materials", Decimal("18.50"), Decimal("25")),
            ("DESK-001", "Work Desk", "piece", "Finished goods", Decimal("3000.00"), Decimal("10")),
            ("CHAIR-001", "Office Chair", "piece", "Finished goods", Decimal("1850.00"), Decimal("8")),
        )
        for sku, name, unit, category_name, cost, reorder in product_specs:
            product = one(session, Product, sku=sku)
            if product is None:
                product = Product(
                    sku=sku,
                    name=name,
                    unit=unit,
                    category_id=categories[category_name].id,
                    unit_cost=cost,
                    reorder_level=reorder,
                )
                session.add(product)
                session.flush()
            products[sku] = product

        stock_specs = (
            ("STEEL-ROD", "RACK-A", Decimal("50"), Decimal("5")),
            ("DESK-001", "PROD", Decimal("50"), Decimal("5")),
            ("CHAIR-001", "PROD", Decimal("4"), Decimal("0")),
        )
        for sku, location_code, on_hand, reserved in stock_specs:
            stock = one(session, Stock, product_id=products[sku].id, location_id=locations[location_code].id)
            if stock is None:
                session.add(Stock(product_id=products[sku].id, location_id=locations[location_code].id, on_hand_quantity=on_hand, reserved_quantity=reserved))

        receipt = one(session, Receipt, reference="MAIN/IN/0001")
        if receipt is None:
            receipt = Receipt(reference="MAIN/IN/0001", warehouse_id=warehouse.id, receive_from="Northwind Metals", schedule_date=date.today() - timedelta(days=2), status=ReceiptStatus.DONE, responsible_id=user.id)
            receipt.items.append(ReceiptItem(product_id=products["STEEL-ROD"].id, location_id=locations["RACK-A"].id, quantity=Decimal("50")))
            session.add(receipt)
            session.flush()

        delivery = one(session, Delivery, reference="MAIN/OUT/0001")
        if delivery is None:
            delivery = Delivery(reference="MAIN/OUT/0001", warehouse_id=warehouse.id, delivery_address="Azure Interior, 20 Market Street", operation_type="Customer shipment", schedule_date=date.today() + timedelta(days=2), status=DeliveryStatus.READY, responsible_id=user.id)
            delivery.items.append(DeliveryItem(product_id=products["DESK-001"].id, location_id=locations["PROD"].id, quantity=Decimal("10")))
            session.add(delivery)
            session.flush()

        completed_delivery = one(session, Delivery, reference="MAIN/OUT/0000")
        if completed_delivery is None:
            completed_delivery = Delivery(reference="MAIN/OUT/0000", warehouse_id=warehouse.id, delivery_address="Northwind Trading, 8 Commerce Lane", operation_type="Customer shipment", schedule_date=date.today() - timedelta(days=1), status=DeliveryStatus.DONE, responsible_id=user.id)
            completed_delivery.items.append(DeliveryItem(product_id=products["CHAIR-001"].id, location_id=locations["PROD"].id, quantity=Decimal("10")))
            session.add(completed_delivery)
            session.flush()

        transfer = one(session, StockTransfer, reference="MAIN/MOVE/0001")
        if transfer is None:
            transfer = StockTransfer(reference="MAIN/MOVE/0001", from_location_id=locations["RACK-A"].id, to_location_id=locations["PROD"].id, responsible_id=user.id, status=TransferStatus.READY)
            transfer.items.append(TransferItem(product_id=products["STEEL-ROD"].id, quantity=Decimal("10")))
            session.add(transfer)
            session.flush()

        adjustment = one(session, StockAdjustment, reference="MAIN/ADJ/0001")
        if adjustment is None:
            adjustment = StockAdjustment(reference="MAIN/ADJ/0001", warehouse_id=warehouse.id, location_id=locations["PROD"].id, reason="Cycle count pending review", status=AdjustmentStatus.DRAFT, responsible_id=user.id)
            adjustment.items.append(StockAdjustmentItem(product_id=products["CHAIR-001"].id, old_quantity=Decimal("4"), new_quantity=Decimal("4"), difference=Decimal("0")))
            session.add(adjustment)
            session.flush()

        if one(session, StockMove, reference="MAIN/IN/0001") is None:
            session.add_all([
                StockMove(reference="MAIN/IN/0001", product_id=products["STEEL-ROD"].id, to_location_id=locations["RACK-A"].id, quantity=Decimal("50"), move_type=MoveType.IN, source_type=SourceType.RECEIPT, source_id=receipt.id, created_by=user.id),
                StockMove(reference="MAIN/OUT/0000", product_id=products["CHAIR-001"].id, from_location_id=locations["PROD"].id, quantity=Decimal("10"), move_type=MoveType.OUT, source_type=SourceType.DELIVERY, source_id=completed_delivery.id, created_by=user.id),
            ])

    print("Demo data is ready.")
    print("Login ID: demo01")
    print("Password: Demo123!")


if __name__ == "__main__":
    seed_demo()
