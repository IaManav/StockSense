from sqlalchemy import func, select

from app.models import Delivery, Product, Receipt, Stock, StockTransfer
from app.models.delivery import DeliveryStatus
from app.models.receipt import ReceiptStatus
from app.models.transfer import TransferStatus


def get_summary(db):
    available = Stock.on_hand_quantity - Stock.reserved_quantity
    return {
        "total_products": db.scalar(select(func.count(func.distinct(Stock.product_id))).where(available > 0)) or 0,
        "low_stock_items": db.scalar(select(func.count(func.distinct(Stock.product_id))).join(Product).where(available > 0, available <= Product.reorder_level)) or 0,
        "out_of_stock_items": db.scalar(select(func.count(func.distinct(Stock.product_id))).where(available <= 0)) or 0,
        "pending_receipts": db.scalar(select(func.count()).select_from(Receipt).where(Receipt.status.in_([ReceiptStatus.DRAFT, ReceiptStatus.READY]))) or 0,
        "pending_deliveries": db.scalar(select(func.count()).select_from(Delivery).where(Delivery.status.in_([DeliveryStatus.DRAFT, DeliveryStatus.WAITING, DeliveryStatus.READY]))) or 0,
        "scheduled_transfers": db.scalar(select(func.count()).select_from(StockTransfer).where(StockTransfer.status.in_([TransferStatus.DRAFT, TransferStatus.READY]))) or 0,
    }
