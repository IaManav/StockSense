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

        staff = one(session, User, login_id="staff01")
        if staff is None:
            staff = User(
                login_id="staff01",
                email="staff@stocksense.local",
                password_hash=generate_password_hash("Staff123!"),
                role=UserRole.STAFF,
            )
            session.add(staff)
            session.flush()

        warehouse = one(session, Warehouse, short_code="MAIN")
        if warehouse is None:
            warehouse = Warehouse(
                name="Main Warehouse", short_code="MAIN", address="12 Industrial Road"
            )
            session.add(warehouse)
            session.flush()

        locations = {}
        for name, code in (("Receiving", "RECV"), ("Rack A", "RACK-A"), ("Production Floor", "PROD"), ("Dispatch", "DISP")):
            location = one(session, Location, warehouse_id=warehouse.id, short_code=code)
            if location is None:
                location = Location(warehouse_id=warehouse.id, name=name, short_code=code)
                session.add(location)
                session.flush()
            locations[code] = location

        branch = one(session, Warehouse, short_code="BRANCH")
        if branch is None:
            branch = Warehouse(name="North Branch Warehouse", short_code="BRANCH", address="48 Logistics Avenue")
            session.add(branch)
            session.flush()
        branch_locations = {}
        for name, code in (("Receiving", "RECV"), ("Bulk Storage", "BULK"), ("Dispatch", "DISP")):
            location = one(session, Location, warehouse_id=branch.id, short_code=code)
            if location is None:
                location = Location(warehouse_id=branch.id, name=name, short_code=code)
                session.add(location)
                session.flush()
            branch_locations[code] = location

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
            ("LAPTOP-15", "Business Laptop 15-inch", "piece", "Finished goods", Decimal("62000.00"), Decimal("5")),
            ("KEYBOARD-01", "Wireless Keyboard", "piece", "Finished goods", Decimal("1450.00"), Decimal("12")),
            ("HDMI-02M", "HDMI Cable 2m", "piece", "Raw materials", Decimal("650.00"), Decimal("20")),
            ("BOX-L", "Large Shipping Box", "piece", "Raw materials", Decimal("85.00"), Decimal("50")),
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
            ("HDMI-02M", "RECV", Decimal("2"), Decimal("2")),
            ("BOX-L", "RECV", Decimal("120"), Decimal("0")),
        )
        for sku, location_code, on_hand, reserved in stock_specs:
            stock = one(session, Stock, product_id=products[sku].id, location_id=locations[location_code].id)
            if stock is None:
                stock = Stock(product_id=products[sku].id, location_id=locations[location_code].id)
                session.add(stock)
            stock.on_hand_quantity = on_hand
            stock.reserved_quantity = reserved

        branch_stock_specs = (
            ("LAPTOP-15", "RECV", Decimal("0"), Decimal("0")),
            ("KEYBOARD-01", "BULK", Decimal("24"), Decimal("8")),
            ("DESK-001", "BULK", Decimal("6"), Decimal("0")),
        )
        for sku, location_code, on_hand, reserved in branch_stock_specs:
            stock = one(session, Stock, product_id=products[sku].id, location_id=branch_locations[location_code].id)
            if stock is None:
                stock = Stock(product_id=products[sku].id, location_id=branch_locations[location_code].id)
                session.add(stock)
            stock.on_hand_quantity = on_hand
            stock.reserved_quantity = reserved

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

        ready_receipt = one(session, Receipt, reference="MAIN/IN/0002")
        if ready_receipt is None:
            ready_receipt = Receipt(reference="MAIN/IN/0002", warehouse_id=warehouse.id, receive_from="Steelworks Supply Co.", schedule_date=date.today() + timedelta(days=1), status=ReceiptStatus.READY, responsible_id=user.id)
            ready_receipt.items.append(ReceiptItem(product_id=products["STEEL-ROD"].id, location_id=locations["RECV"].id, quantity=Decimal("100")))
            session.add(ready_receipt)

        draft_receipt = one(session, Receipt, reference="MAIN/IN/0003")
        if draft_receipt is None:
            draft_receipt = Receipt(reference="MAIN/IN/0003", warehouse_id=warehouse.id, receive_from="Cable Depot", schedule_date=date.today() + timedelta(days=4), status=ReceiptStatus.DRAFT, responsible_id=staff.id)
            draft_receipt.items.append(ReceiptItem(product_id=products["HDMI-02M"].id, location_id=locations["RECV"].id, quantity=Decimal("40")))
            session.add(draft_receipt)

        waiting_delivery = one(session, Delivery, reference="MAIN/OUT/0002")
        if waiting_delivery is None:
            waiting_delivery = Delivery(reference="MAIN/OUT/0002", warehouse_id=warehouse.id, delivery_address="Contoso Retail, 99 Market Road", operation_type="Customer shipment", schedule_date=date.today() - timedelta(days=1), status=DeliveryStatus.WAITING, responsible_id=staff.id)
            waiting_delivery.items.append(DeliveryItem(product_id=products["DESK-001"].id, location_id=locations["PROD"].id, quantity=Decimal("75")))
            session.add(waiting_delivery)

        draft_delivery = one(session, Delivery, reference="MAIN/OUT/0003")
        if draft_delivery is None:
            draft_delivery = Delivery(reference="MAIN/OUT/0003", warehouse_id=warehouse.id, delivery_address="Fabrikam Studio, 15 Design Street", operation_type="Customer shipment", schedule_date=date.today() + timedelta(days=3), status=DeliveryStatus.DRAFT, responsible_id=staff.id)
            draft_delivery.items.append(DeliveryItem(product_id=products["CHAIR-001"].id, location_id=locations["PROD"].id, quantity=Decimal("2")))
            session.add(draft_delivery)

        branch_delivery = one(session, Delivery, reference="BRANCH/OUT/0001")
        if branch_delivery is None:
            branch_delivery = Delivery(reference="BRANCH/OUT/0001", warehouse_id=branch.id, delivery_address="Globex Office Park, 7 Business Way", operation_type="Customer shipment", schedule_date=date.today() + timedelta(days=2), status=DeliveryStatus.READY, responsible_id=staff.id)
            branch_delivery.items.append(DeliveryItem(product_id=products["KEYBOARD-01"].id, location_id=branch_locations["BULK"].id, quantity=Decimal("8")))
            session.add(branch_delivery)

        transfer = one(session, StockTransfer, reference="MAIN/MOVE/0001")
        if transfer is None:
            transfer = StockTransfer(reference="MAIN/MOVE/0001", from_location_id=locations["RACK-A"].id, to_location_id=locations["PROD"].id, responsible_id=user.id, status=TransferStatus.READY)
            transfer.items.append(TransferItem(product_id=products["STEEL-ROD"].id, quantity=Decimal("10")))
            session.add(transfer)
            session.flush()

        draft_transfer = one(session, StockTransfer, reference="MAIN/MOVE/0002")
        if draft_transfer is None:
            draft_transfer = StockTransfer(reference="MAIN/MOVE/0002", from_location_id=locations["RACK-A"].id, to_location_id=locations["DISP"].id, responsible_id=staff.id, status=TransferStatus.DRAFT)
            draft_transfer.items.append(TransferItem(product_id=products["STEEL-ROD"].id, quantity=Decimal("5")))
            session.add(draft_transfer)

        branch_transfer = one(session, StockTransfer, reference="BRANCH/MOVE/0001")
        if branch_transfer is None:
            branch_transfer = StockTransfer(reference="BRANCH/MOVE/0001", from_location_id=branch_locations["BULK"].id, to_location_id=branch_locations["DISP"].id, responsible_id=staff.id, status=TransferStatus.DONE)
            branch_transfer.items.append(TransferItem(product_id=products["KEYBOARD-01"].id, quantity=Decimal("4")))
            session.add(branch_transfer)
            session.flush()

        adjustment = one(session, StockAdjustment, reference="MAIN/ADJ/0001")
        if adjustment is None:
            adjustment = StockAdjustment(reference="MAIN/ADJ/0001", warehouse_id=warehouse.id, location_id=locations["PROD"].id, reason="Cycle count pending review", status=AdjustmentStatus.DRAFT, responsible_id=user.id)
            adjustment.items.append(StockAdjustmentItem(product_id=products["CHAIR-001"].id, old_quantity=Decimal("4"), new_quantity=Decimal("4"), difference=Decimal("0")))
            session.add(adjustment)
            session.flush()

        completed_adjustment = one(session, StockAdjustment, reference="MAIN/ADJ/0002")
        if completed_adjustment is None:
            completed_adjustment = StockAdjustment(reference="MAIN/ADJ/0002", warehouse_id=warehouse.id, location_id=locations["PROD"].id, reason="Monthly cycle count correction", status=AdjustmentStatus.DONE, responsible_id=staff.id)
            completed_adjustment.items.append(StockAdjustmentItem(product_id=products["DESK-001"].id, old_quantity=Decimal("48"), new_quantity=Decimal("50"), difference=Decimal("2")))
            session.add(completed_adjustment)
            session.flush()

        if one(session, StockMove, reference="MAIN/IN/0001") is None:
            session.add_all([
                StockMove(reference="MAIN/IN/0001", product_id=products["STEEL-ROD"].id, to_location_id=locations["RACK-A"].id, quantity=Decimal("50"), move_type=MoveType.IN, source_type=SourceType.RECEIPT, source_id=receipt.id, created_by=user.id),
                StockMove(reference="MAIN/OUT/0000", product_id=products["CHAIR-001"].id, from_location_id=locations["PROD"].id, quantity=Decimal("10"), move_type=MoveType.OUT, source_type=SourceType.DELIVERY, source_id=completed_delivery.id, created_by=user.id),
            ])

        extra_moves = (
            StockMove(reference="BRANCH/MOVE/0001", product_id=products["KEYBOARD-01"].id, from_location_id=branch_locations["BULK"].id, to_location_id=branch_locations["DISP"].id, quantity=Decimal("4"), move_type=MoveType.TRANSFER, source_type=SourceType.TRANSFER, source_id=branch_transfer.id, created_by=staff.id),
            StockMove(reference="MAIN/ADJ/0002", product_id=products["DESK-001"].id, to_location_id=locations["PROD"].id, quantity=Decimal("2"), move_type=MoveType.ADJUSTMENT, source_type=SourceType.ADJUSTMENT, source_id=completed_adjustment.id, created_by=staff.id),
            StockMove(reference="BRANCH/IN/0001", product_id=products["LAPTOP-15"].id, to_location_id=branch_locations["BULK"].id, quantity=Decimal("12"), move_type=MoveType.IN, source_type=SourceType.RECEIPT, source_id=receipt.id, created_by=user.id),
        )
        for move in extra_moves:
            if one(session, StockMove, reference=move.reference) is None:
                session.add(move)

    print("Demo data is ready.")
    print("Login ID: demo01")
    print("Password: Demo123!")


if __name__ == "__main__":
    seed_demo()
