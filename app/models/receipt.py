import uuid
import enum
from datetime import date
from decimal import Decimal
from sqlalchemy import (
    String,
    Date,
    ForeignKey,
    Enum,
    Numeric,
    DECIMAL
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReceiptStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    reference: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False
    )

    receive_from: Mapped[str | None] = mapped_column(
        String(255)
    )

    schedule_date: Mapped[date | None] = mapped_column(
        Date
    )

    status: Mapped[ReceiptStatus] = mapped_column(
        Enum(ReceiptStatus),
        default=ReceiptStatus.DRAFT
    )

    responsible_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False
    )

    receipt = relationship("Receipt", back_populates="items")
