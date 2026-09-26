import uuid
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Numeric,
    Boolean,
    ForeignKey
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True
    )

    unit: Mapped[str] = mapped_column(
        String(50),
        default="piece"
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=0
    )

    reorder_level: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=0
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )