import uuid
from decimal import Decimal

from sqlalchemy import (
    Numeric,
    ForeignKey,
    UniqueConstraint
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Stock(Base):
    __tablename__ = "stock"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False
    )

    on_hand_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        default=0,
        nullable=False
    )

    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        default=0,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "location_id",
            name="uq_product_location"
        ),
    )

    @property
    def free_to_use(self):
        return (
            self.on_hand_quantity -
            self.reserved_quantity
        )