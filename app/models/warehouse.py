import uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    short_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )

    locations = relationship(
        "Location",
        back_populates="warehouse",
        cascade="all, delete-orphan"
    )

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("warehouses.id"),
    nullable=False
)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    short_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    warehouse = relationship(
        "Warehouse",
        back_populates="locations"
    )