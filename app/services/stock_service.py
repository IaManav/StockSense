from decimal import Decimal

from extensions import db
from models.stock import Stock
from models.product import Product
from models.location import Location


def get_or_create_stock(product_id, location_id):
    stock = Stock.query.filter_by(
        product_id=product_id,
        location_id=location_id,
    ).first()

    if not stock:
        stock = Stock(
            product_id=product_id,
            location_id=location_id,
            on_hand_quantity=Decimal("0"),
            reserved_quantity=Decimal("0"),
        )
        db.session.add(stock)
        db.session.flush()

    return stock


def get_stock(product_id=None, location_id=None, warehouse_id=None):
    query = Stock.query

    if product_id:
        query = query.filter(Stock.product_id == product_id)

    if location_id:
        query = query.filter(Stock.location_id == location_id)

    if warehouse_id:
        query = query.join(Location).filter(
            Location.warehouse_id == warehouse_id
        )

    return query.all()


def get_product_stock(product_id):
    if not db.session.get(Product, product_id):
        raise ValueError("Product not found")
    return get_stock(product_id=product_id)


def get_location_stock(location_id):
    if not db.session.get(Location, location_id):
        raise ValueError("Location not found")
    return get_stock(location_id=location_id)


def get_warehouse_stock(warehouse_id):
    return get_stock(warehouse_id=warehouse_id)


def free_to_use(stock):
    return stock.on_hand_quantity - stock.reserved_quantity


def low_stock():
    query = (
        Stock.query
        .join(Product)
        .filter(
            (Stock.on_hand_quantity - Stock.reserved_quantity)
            <= Product.reorder_level
        )
    )
    return query.all()


def out_of_stock():
    return (
        Stock.query
        .filter(
            (Stock.on_hand_quantity - Stock.reserved_quantity)
            <= Decimal("0")
        )
        .all()
    )


def increase_stock(product_id, location_id, quantity):
    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    stock = get_or_create_stock(product_id, location_id)
    stock.on_hand_quantity += quantity
    return stock


def decrease_stock(product_id, location_id, quantity):
    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")

    stock = get_or_create_stock(product_id, location_id)

    if free_to_use(stock) < quantity:
        raise ValueError("Insufficient available stock")

    stock.on_hand_quantity -= quantity
    return stock


def transfer_stock(product_id, from_location_id, to_location_id, quantity):
    quantity = Decimal(str(quantity))

    if from_location_id == to_location_id:
        raise ValueError("Source and destination locations must be different")

    source = decrease_stock(product_id, from_location_id, quantity)
    destination = increase_stock(product_id, to_location_id, quantity)

    return source, destination
