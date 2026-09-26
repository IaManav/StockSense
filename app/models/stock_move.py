import uuid
import enum
from datetime import datetime, timezone

from app.database import Base
from sqlalchemy import (
    String,
    Date,
    ForeignKey,
    Enum,
    Numeric,
    DECIMAL
)

from sqlalchemy.orm import Mapped, mapped_column

class MoveType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class SourceType(str, enum.Enum):
    RECEIPT = "RECEIPT"
    DELIVERY = "DELIVERY"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class StockMove(Base):
    __tablename__ = "stock_moves"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    from_location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("locations.id")
    )

    to_location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("locations.id")
    )

    quantity: Mapped[DECIMAL] = mapped_column(
        Numeric(14, 3),
        nullable=False
    )

    move_type: Mapped[MoveType] = mapped_column(
        Enum(MoveType),
        nullable=False
    )

    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType),
        nullable=False
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
