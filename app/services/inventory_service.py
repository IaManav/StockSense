from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Delivery,
    DeliveryItem,
    Product,
    Receipt,
    ReceiptItem,
    Stock,
    StockAdjustment,
    StockAdjustmentItem,
    StockMove,
    StockTransfer,
    TransferItem,
)
from app.models.delivery import DeliveryStatus
from app.models.receipt import ReceiptStatus
from app.models.adjustment import AdjustmentStatus
from app.models.stock_move import MoveType, SourceType
from app.models.transfer import TransferStatus


class NotFoundError(ValueError):
    pass


T = TypeVar("T")


def require(db: Session, model: type[T], record_id: UUID, label: str) -> T:
    record = db.get(model, record_id)
    if record is None:
        raise NotFoundError(f"{label} not found")
    return record


def decimal_value(value: object, field: str, *, allow_zero: bool = False) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field} must be a number") from exc
    if result < 0 or (result == 0 and not allow_zero):
        raise ValueError(f"{field} must be greater than zero")
    return result


def get_or_create_stock(db: Session, product_id: UUID, location_id: UUID) -> Stock:
    stock = db.scalar(
        select(Stock).where(Stock.product_id == product_id, Stock.location_id == location_id)
    )
    if stock is None:
        stock = Stock(product_id=product_id, location_id=location_id, on_hand_quantity=Decimal("0"), reserved_quantity=Decimal("0"))
        db.add(stock)
        db.flush()
    return stock


def change_stock(db: Session, product_id: UUID, location_id: UUID, quantity: object, direction: int) -> Stock:
    amount = decimal_value(quantity, "quantity")
    stock = get_or_create_stock(db, product_id, location_id)
    if direction < 0 and stock.free_to_use < amount:
        raise ValueError("Insufficient available stock")
    stock.on_hand_quantity += amount * direction
    return stock


def create_move(
    db: Session,
    *,
    reference: str,
    product_id: UUID,
    quantity: Decimal,
    move_type: MoveType,
    source_type: SourceType,
    source_id: UUID,
    created_by: UUID,
    from_location_id: UUID | None = None,
    to_location_id: UUID | None = None,
) -> StockMove:
    move = StockMove(
        reference=reference,
        product_id=product_id,
        quantity=quantity,
        move_type=move_type,
        source_type=source_type,
        source_id=source_id,
        created_by=created_by,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
    )
    db.add(move)
    return move


def validate_receipt(db: Session, receipt_id: UUID, created_by: UUID) -> Receipt:
    receipt = require(db, Receipt, receipt_id, "Receipt")
    if receipt.status != ReceiptStatus.READY:
        raise ValueError("Only READY receipts can be validated")
    if not receipt.items:
        raise ValueError("Receipt must contain at least one item")
    for item in receipt.items:
        change_stock(db, item.product_id, item.location_id, item.quantity, 1)
        create_move(db, reference=receipt.reference, product_id=item.product_id, quantity=item.quantity,
                    move_type=MoveType.IN, source_type=SourceType.RECEIPT, source_id=receipt.id,
                    created_by=created_by, to_location_id=item.location_id)
    receipt.status = ReceiptStatus.DONE
    return receipt


def validate_delivery(db: Session, delivery_id: UUID, created_by: UUID) -> Delivery:
    delivery = require(db, Delivery, delivery_id, "Delivery")
    if delivery.status != DeliveryStatus.READY:
        raise ValueError("Only READY deliveries can be validated")
    if not delivery.items:
        raise ValueError("Delivery must contain at least one item")
    for item in delivery.items:
        change_stock(db, item.product_id, item.location_id, item.quantity, -1)
        create_move(db, reference=delivery.reference, product_id=item.product_id, quantity=item.quantity,
                    move_type=MoveType.OUT, source_type=SourceType.DELIVERY, source_id=delivery.id,
                    created_by=created_by, from_location_id=item.location_id)
    delivery.status = DeliveryStatus.DONE
    return delivery


def validate_adjustment(db: Session, adjustment_id: UUID, created_by: UUID) -> StockAdjustment:
    adjustment = require(db, StockAdjustment, adjustment_id, "Adjustment")
    if adjustment.status != AdjustmentStatus.DRAFT:
        raise ValueError("Only DRAFT adjustments can be validated")
    if not adjustment.items:
        raise ValueError("Adjustment must contain at least one item")
    for item in adjustment.items:
        stock = get_or_create_stock(db, item.product_id, adjustment.location_id)
        difference = item.new_quantity - stock.on_hand_quantity
        stock.on_hand_quantity = item.new_quantity
        item.old_quantity = stock.on_hand_quantity - difference
        item.difference = difference
        create_move(db, reference=adjustment.reference, product_id=item.product_id, quantity=abs(difference),
                    move_type=MoveType.ADJUSTMENT, source_type=SourceType.ADJUSTMENT, source_id=adjustment.id,
                    created_by=created_by,
                    from_location_id=adjustment.location_id if difference < 0 else None,
                    to_location_id=adjustment.location_id if difference > 0 else None)
    adjustment.status = AdjustmentStatus.DONE
    return adjustment


def validate_transfer(db: Session, transfer_id: UUID, created_by: UUID) -> StockTransfer:
    transfer = require(db, StockTransfer, transfer_id, "Transfer")
    if transfer.status != TransferStatus.READY:
        raise ValueError("Only READY transfers can be validated")
    if not transfer.items:
        raise ValueError("Transfer must contain at least one item")
    for item in transfer.items:
        change_stock(db, item.product_id, transfer.from_location_id, item.quantity, -1)
        change_stock(db, item.product_id, transfer.to_location_id, item.quantity, 1)
        create_move(db, reference=transfer.reference, product_id=item.product_id, quantity=item.quantity,
                    move_type=MoveType.TRANSFER, source_type=SourceType.TRANSFER, source_id=transfer.id,
                    created_by=created_by, from_location_id=transfer.from_location_id,
                    to_location_id=transfer.to_location_id)
    transfer.status = TransferStatus.DONE
    return transfer
