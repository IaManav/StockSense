import uuid
import enum
from datetime import date

from sqlalchemy import (
    String,
    Date,
    ForeignKey,
    Enum,
    Text,
    Numeric,
    DECIMAL
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeliveryStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    WAITING = "WAITING"
    READY = "READY"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class Delivery(Base):
    __tablename__ = "deliveries"

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

    delivery_address: Mapped[str | None] = mapped_column(
        Text
    )

    schedule_date: Mapped[date | None] = mapped_column(
        Date
    )

    operation_type: Mapped[str | None] = mapped_column(
        String(100)
    )

    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus),
        default=DeliveryStatus.DRAFT
    )

    responsible_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    items = relationship("DeliveryItem", back_populates="delivery", cascade="all, delete-orphan")

class DeliveryItem(Base):
    __tablename__ = "delivery_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deliveries.id", ondelete="CASCADE"),
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

    quantity: Mapped[DECIMAL] = mapped_column(
        Numeric(14, 3),
        nullable=False
    )

    delivery = relationship("Delivery", back_populates="items")
