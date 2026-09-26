import uuid
import enum
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Numeric,
    ForeignKey,
    Enum,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AdjustmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    reference: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id"),
        nullable=False,
    )

    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[AdjustmentStatus] = mapped_column(
        Enum(AdjustmentStatus),
        default=AdjustmentStatus.DRAFT,
        nullable=False,
    )

    responsible_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )


class StockAdjustmentItem(Base):
    __tablename__ = "stock_adjustment_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    adjustment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "stock_adjustments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    old_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    new_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    difference: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )