from datetime import date, datetime, timedelta, timezone
import secrets
import re
from typing import Any
from uuid import UUID

from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Delivery, DeliveryItem, Location, Product, Receipt, ReceiptItem, Stock, StockAdjustment, StockAdjustmentItem, StockMove, User, Warehouse
from app.models import PasswordResetCode, StockTransfer, TransferItem
from app.models.adjustment import AdjustmentStatus
from app.models.delivery import DeliveryStatus
from app.models.receipt import ReceiptStatus
from app.models.transfer import TransferStatus
from app.services.inventory_service import NotFoundError, decimal_value, get_or_create_stock, require, validate_adjustment, validate_delivery, validate_receipt, validate_transfer
from app.validation import validate_email, validate_password
from werkzeug.security import check_password_hash, generate_password_hash


api_bp = Blueprint("api", __name__)


def db() -> Session:
    return get_db()


def payload() -> dict[str, Any]:
    return request.get_json(silent=True) or {}


def data(model: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name == "password_hash":
            continue
        value = getattr(model, column.name)
        result[column.name] = value.value if hasattr(value, "value") else value
    return result


def required(body: dict[str, Any], *fields: str) -> None:
    missing = [field for field in fields if body.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")


def as_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a UUID") from exc


def as_date(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def get_required(model: type, record_id: UUID, label: str):
    try:
        return require(db(), model, record_id, label)
    except NotFoundError as exc:
        return fail(str(exc), 404)


def commit() -> None:
    try:
        db().commit()
    except IntegrityError as exc:
        db().rollback()
        raise ValueError("A record with those unique values already exists") from exc


def fail(message: str, code: int = 400):
    return jsonify(error=message), code


@api_bp.errorhandler(ValueError)
def value_error(error: ValueError):
    db().rollback()
    return fail(str(error), 422)


def logged_in_user() -> User | None:
    user_id = session.get("user_id")
    return db().get(User, UUID(user_id)) if user_id else None


@api_bp.post("/auth/signup")
def signup():
    body = payload()
    required(body, "login_id", "email", "password")
    login_id = body["login_id"].strip()
    if not 6 <= len(login_id) <= 12:
        return fail("login_id must be 6-12 characters", 422)
    email = validate_email(body["email"])
    validate_password(body["password"])
    if db().scalar(select(User).where(User.login_id == login_id)):
        return fail("Login ID already exists. Choose a different Login ID.", 409)
    if db().scalar(select(User).where(User.email == email)):
        return fail("Email already exists. Use a different email address.", 409)
    user = User(login_id=login_id, email=email, password_hash=generate_password_hash(body["password"]))
    db().add(user)
    commit()
    session["user_id"] = str(user.id)
    return jsonify(data(user)), 201


@api_bp.post("/auth/login")
def login():
    body = payload()
    required(body, "login_id", "password")
    user = db().scalar(select(User).where(User.login_id == body["login_id"].strip()))
    if user is None or not check_password_hash(user.password_hash, body["password"]):
        return fail("Invalid login ID or password. Check your credentials and try again.", 401)
    session["user_id"] = str(user.id)
    return jsonify(data(user))


@api_bp.post("/auth/forgot-password")
def forgot_password():
    body = payload()
    required(body, "email")
    email = validate_email(body["email"])
    user = db().scalar(select(User).where(User.email == email))
    response = {"message": "If an account exists, a password reset code has been created."}
    if user is None:
        return jsonify(response)

    code = f"{secrets.randbelow(1_000_000):06d}"
    reset_code = PasswordResetCode(
        email=email,
        code_hash=generate_password_hash(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db().add(reset_code)
    commit()
    if current_app.debug:
        response["development_otp"] = code
    return jsonify(response)


@api_bp.post("/auth/reset-password")
def reset_password():
    body = payload()
    required(body, "email", "otp", "new_password")
    email = validate_email(body["email"])
    new_password = validate_password(body["new_password"])
    now = datetime.now(timezone.utc)
    reset_code = db().scalar(
        select(PasswordResetCode)
        .where(
            PasswordResetCode.email == email,
            PasswordResetCode.used_at.is_(None),
            PasswordResetCode.expires_at > now,
        )
        .order_by(PasswordResetCode.created_at.desc())
    )
    if reset_code is None or not check_password_hash(reset_code.code_hash, str(body["otp"]).strip()):
        return fail("Invalid or expired password reset code", 400)
    user = db().scalar(select(User).where(User.email == email))
    if user is None:
        return fail("Invalid or expired password reset code", 400)
    user.password_hash = generate_password_hash(new_password)
    reset_code.used_at = now
    commit()
    return jsonify(message="Password reset successful")


@api_bp.post("/auth/logout")
def logout():
    session.pop("user_id", None)
    return jsonify(message="Logout successful")


@api_bp.get("/auth/me")
@api_bp.get("/users/me")
def current_user():
    user = logged_in_user()
    if user is None:
        return fail("Authentication required", 401)
    return jsonify(data(user))


@api_bp.put("/users/me")
def update_current_user():
    user = logged_in_user()
    if user is None:
        return fail("Authentication required", 401)
    body = payload()
    if "login_id" in body:
        login_id = body["login_id"].strip()
        existing = db().scalar(select(User).where(User.login_id == login_id, User.id != user.id))
        if existing:
            return fail("login_id already exists", 409)
        user.login_id = login_id
    if "email" in body:
        email = validate_email(body["email"])
        existing = db().scalar(select(User).where(User.email == email, User.id != user.id))
        if existing:
            return fail("email already exists", 409)
        user.email = email
    commit()
    return jsonify(data(user))


@api_bp.put("/users/me/password")
def change_current_password():
    user = logged_in_user()
    if user is None:
        return fail("Authentication required", 401)
    body = payload()
    required(body, "old_password", "new_password")
    if not check_password_hash(user.password_hash, body["old_password"]):
        return fail("Current password is incorrect", 403)
    user.password_hash = generate_password_hash(validate_password(body["new_password"]))
    commit()
    return jsonify(message="Password updated")


@api_bp.post("/users")
def create_user():
    body = payload()
    required(body, "login_id", "email", "password_hash")
    user = User(login_id=body["login_id"].strip(), email=validate_email(body["email"]), password_hash=body["password_hash"], role=body.get("role", "STAFF"))
    db().add(user)
    commit()
    return jsonify(data(user)), 201


@api_bp.get("/warehouses")
def list_warehouses():
    return jsonify(items=[data(item) for item in db().scalars(select(Warehouse).order_by(Warehouse.name)).all()])


@api_bp.post("/warehouses")
def create_warehouse():
    body = payload()
    required(body, "name", "short_code")
    warehouse = Warehouse(name=body["name"], short_code=body["short_code"].upper(), address=body.get("address"), is_active=body.get("is_active", True))
    db().add(warehouse)
    commit()
    return jsonify(data(warehouse)), 201


@api_bp.get("/warehouses/<uuid:warehouse_id>/locations")
def list_warehouse_locations(warehouse_id: UUID):
    result = get_required(Warehouse, warehouse_id, "Warehouse")
    if not isinstance(result, Warehouse):
        return result
    items = db().scalars(select(Location).where(Location.warehouse_id == warehouse_id).order_by(Location.name)).all()
    return jsonify(items=[data(item) for item in items])


@api_bp.get("/locations")
def list_locations():
    warehouse_id = request.args.get("warehouse_id", type=UUID)
    query = select(Location).order_by(Location.name)
    if warehouse_id:
        query = query.where(Location.warehouse_id == warehouse_id)
    items = []
    for item in db().scalars(query).all():
        record = data(item)
        contact = db().get(User, item.created_by)
        from_location = db().get(Location, item.from_location_id) if item.from_location_id else None
        to_location = db().get(Location, item.to_location_id) if item.to_location_id else None
        record["date"] = item.created_at
        record["contact"] = contact.login_id if contact else str(item.created_by)
        record["from"] = from_location.short_code if from_location else "-"
        record["to"] = to_location.short_code if to_location else "-"
        record["status"] = item.move_type.value
        items.append(record)
    return jsonify(items=items)


@api_bp.post("/locations")
def create_location():
    body = payload()
    required(body, "warehouse_id", "name", "short_code")
    warehouse_id = as_uuid(body["warehouse_id"], "warehouse_id")
    result = get_required(Warehouse, warehouse_id, "Warehouse")
    if not isinstance(result, Warehouse):
        return result
    location = Location(warehouse_id=warehouse_id, name=body["name"], short_code=body["short_code"].upper())
    db().add(location)
    commit()
    return jsonify(data(location)), 201


@api_bp.get("/categories")
def list_categories():
    return jsonify(items=[data(item) for item in db().scalars(select(Category).order_by(Category.name)).all()])


@api_bp.post("/categories")
def create_category():
    body = payload()
    required(body, "name")
    category = Category(name=body["name"], description=body.get("description"))
    db().add(category)
    commit()
    return jsonify(data(category)), 201


@api_bp.get("/products")
def list_products():
    query = select(Product).order_by(Product.name)
    search = request.args.get("search")
    if search:
        query = query.where(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))
    if category_id := request.args.get("category_id", type=UUID):
        query = query.where(Product.category_id == category_id)
    if (is_active := request.args.get("is_active")) is not None:
        query = query.where(Product.is_active == (is_active.lower() == "true"))
    return jsonify(items=[data(item) for item in db().scalars(query).all()])


@api_bp.post("/products")
def create_product():
    body = payload()
    required(body, "sku", "name")
    category_id = as_uuid(body["category_id"], "category_id") if body.get("category_id") else None
    if category_id:
        result = get_required(Category, category_id, "Category")
        if not isinstance(result, Category):
            return result
    product = Product(sku=body["sku"].upper(), name=body["name"], description=body.get("description"), category_id=category_id, unit=body.get("unit", "piece"), unit_cost=decimal_value(body.get("unit_cost", 0), "unit_cost", allow_zero=True), reorder_level=decimal_value(body.get("reorder_level", 0), "reorder_level", allow_zero=True), is_active=body.get("is_active", True))
    db().add(product)
    commit()
    return jsonify(data(product)), 201


@api_bp.get("/stock")
def list_stock():
    query = select(Stock)
    if product_id := request.args.get("product_id", type=UUID):
        query = query.where(Stock.product_id == product_id)
    if location_id := request.args.get("location_id", type=UUID):
        query = query.where(Stock.location_id == location_id)
    if warehouse_id := request.args.get("warehouse_id", type=UUID):
        query = query.join(Location).where(Location.warehouse_id == warehouse_id)
    return jsonify(items=[{**data(item), "free_to_use": item.free_to_use} for item in db().scalars(query).all()])


@api_bp.post("/stock/<uuid:product_id>/<uuid:location_id>/receive")
def receive_stock(product_id: UUID, location_id: UUID):
    body = payload()
    required(body, "quantity")
    if not isinstance(get_required(Product, product_id, "Product"), Product) or not isinstance(get_required(Location, location_id, "Location"), Location):
        return fail("Product or location not found", 404)
    stock = get_or_create_stock(db(), product_id, location_id)
    stock.on_hand_quantity += decimal_value(body["quantity"], "quantity")
    commit()
    return jsonify({**data(stock), "free_to_use": stock.free_to_use})


def next_operation_reference(model: type, warehouse: Warehouse, operation_code: str) -> str:
    pattern = re.compile(rf"^{re.escape(warehouse.short_code)}/{operation_code}/(\d+)$")
    references = db().scalars(select(model.reference).where(model.reference.like(f"{warehouse.short_code}/{operation_code}/%"))).all()
    numbers = [int(match.group(1)) for value in references if (match := pattern.match(value))]
    return f"{warehouse.short_code}/{operation_code}/{(max(numbers, default=0) + 1):03d}"


def create_operation(model: type, body: dict[str, Any]):
    required(body, "warehouse_id", "responsible_id")
    warehouse_id = as_uuid(body["warehouse_id"], "warehouse_id")
    responsible_id = as_uuid(body["responsible_id"], "responsible_id")
    warehouse = get_required(Warehouse, warehouse_id, "Warehouse")
    if not isinstance(warehouse, Warehouse) or not isinstance(get_required(User, responsible_id, "User"), User):
        return fail("Warehouse or user not found", 404)
    operation_code = "IN" if model is Receipt else "OUT"
    reference = body.get("reference") or next_operation_reference(model, warehouse, operation_code)
    fields = {"reference": reference, "warehouse_id": warehouse_id, "responsible_id": responsible_id, "schedule_date": as_date(body.get("schedule_date"), "schedule_date")}
    if model is Receipt:
        fields["receive_from"] = body.get("receive_from")
    else:
        fields.update(delivery_address=body.get("delivery_address"), operation_type=body.get("operation_type"))
    operation = model(**fields)
    db().add(operation)
    commit()
    return jsonify(data(operation)), 201


@api_bp.post("/receipts")
def create_receipt():
    return create_operation(Receipt, payload())


@api_bp.get("/receipts")
def list_receipts():
    query = select(Receipt).order_by(Receipt.id.desc())
    items = []
    for item in db().scalars(query).all():
        record = data(item)
        warehouse = db().get(Warehouse, item.warehouse_id)
        locations = []
        for line in item.items:
            location = db().get(Location, line.location_id)
            if location:
                locations.append(f"{warehouse.short_code}/{location.short_code}")
        contact = db().get(User, item.responsible_id)
        record["to_location"] = ", ".join(dict.fromkeys(locations)) or "-"
        record["contact"] = contact.login_id if contact else str(item.responsible_id)
        items.append(record)
    return jsonify(items=items)


def receipt_details(receipt: Receipt) -> dict[str, Any]:
    record = data(receipt)
    warehouse = db().get(Warehouse, receipt.warehouse_id)
    responsible = db().get(User, receipt.responsible_id)
    record["to_location"] = "-"
    record["contact"] = responsible.login_id if responsible else str(receipt.responsible_id)
    record["items"] = []
    locations = []
    for line in receipt.items:
        product = db().get(Product, line.product_id)
        location = db().get(Location, line.location_id)
        destination = f"{warehouse.short_code}/{location.short_code}" if warehouse and location else "-"
        locations.append(destination)
        record["items"].append({
            "id": str(line.id),
            "product_id": str(line.product_id),
            "product": product.name if product else "-",
            "sku": product.sku if product else "-",
            "quantity": line.quantity,
            "to_location": destination,
        })
    record["to_location"] = ", ".join(dict.fromkeys(locations)) or "-"
    return record


@api_bp.get("/receipts/<uuid:receipt_id>")
def get_receipt(receipt_id: UUID):
    receipt = get_required(Receipt, receipt_id, "Receipt")
    if not isinstance(receipt, Receipt):
        return receipt
    return jsonify(receipt_details(receipt))


@api_bp.post("/receipts/<uuid:receipt_id>/cancel")
def cancel_receipt(receipt_id: UUID):
    receipt = get_required(Receipt, receipt_id, "Receipt")
    if not isinstance(receipt, Receipt):
        return receipt
    if receipt.status == ReceiptStatus.DONE:
        return fail("A received receipt cannot be cancelled", 409)
    receipt.status = ReceiptStatus.CANCELLED
    commit()
    return jsonify(data(receipt))


@api_bp.post("/deliveries")
def create_delivery():
    return create_operation(Delivery, payload())


@api_bp.get("/deliveries")
def list_deliveries():
    query = select(Delivery).order_by(Delivery.id.desc())
    items = []
    for item in db().scalars(query).all():
        record = data(item)
        warehouse = db().get(Warehouse, item.warehouse_id)
        contact = db().get(User, item.responsible_id)
        record["from_warehouse"] = warehouse.short_code if warehouse else "-"
        record["to_address"] = item.delivery_address or "-"
        record["contact"] = contact.login_id if contact else str(item.responsible_id)
        items.append(record)
    return jsonify(items=items)


def delivery_details(delivery: Delivery) -> dict[str, Any]:
    record = data(delivery)
    warehouse = db().get(Warehouse, delivery.warehouse_id)
    responsible = db().get(User, delivery.responsible_id)
    record["from_warehouse"] = warehouse.short_code if warehouse else "-"
    record["contact"] = responsible.login_id if responsible else str(delivery.responsible_id)
    record["items"] = []
    for line in delivery.items:
        product = db().get(Product, line.product_id)
        location = db().get(Location, line.location_id)
        stock = db().scalar(select(Stock).where(Stock.product_id == line.product_id, Stock.location_id == line.location_id))
        available = stock.free_to_use if stock else 0
        record["items"].append({
            "id": str(line.id),
            "product_id": str(line.product_id),
            "product": product.name if product else "-",
            "sku": product.sku if product else "-",
            "quantity": line.quantity,
            "location": location.short_code if location else "-",
            "available_quantity": available,
            "insufficient_stock": line.quantity > available,
        })
    return record


@api_bp.get("/deliveries/<uuid:delivery_id>")
def get_delivery(delivery_id: UUID):
    delivery = get_required(Delivery, delivery_id, "Delivery")
    if not isinstance(delivery, Delivery):
        return delivery
    return jsonify(delivery_details(delivery))


@api_bp.post("/deliveries/<uuid:delivery_id>/cancel")
def cancel_delivery(delivery_id: UUID):
    delivery = get_required(Delivery, delivery_id, "Delivery")
    if not isinstance(delivery, Delivery):
        return delivery
    if delivery.status == DeliveryStatus.DONE:
        return fail("A delivered order cannot be cancelled", 409)
    delivery.status = DeliveryStatus.CANCELLED
    commit()
    return jsonify(data(delivery))


def add_operation_item(operation_model: type, item_model: type, operation_id: UUID, body: dict[str, Any]):
    operation = get_required(operation_model, operation_id, operation_model.__name__)
    if not isinstance(operation, operation_model):
        return operation
    if operation.status.name != "DRAFT":
        return fail("Only DRAFT operations can be edited", 409)
    required(body, "product_id", "location_id", "quantity")
    product_id = as_uuid(body["product_id"], "product_id")
    location_id = as_uuid(body["location_id"], "location_id")
    if not isinstance(get_required(Product, product_id, "Product"), Product) or not isinstance(get_required(Location, location_id, "Location"), Location):
        return fail("Product or location not found", 404)
    item = item_model(product_id=product_id, location_id=location_id, quantity=decimal_value(body["quantity"], "quantity"))
    if operation_model is Receipt:
        item.receipt_id = operation_id
    else:
        item.delivery_id = operation_id
    db().add(item)
    commit()
    return jsonify(data(item)), 201


@api_bp.post("/receipts/<uuid:receipt_id>/items")
def add_receipt_item(receipt_id: UUID):
    return add_operation_item(Receipt, ReceiptItem, receipt_id, payload())


@api_bp.post("/deliveries/<uuid:delivery_id>/items")
def add_delivery_item(delivery_id: UUID):
    return add_operation_item(Delivery, DeliveryItem, delivery_id, payload())


def mark_ready(model: type, operation_id: UUID):
    operation = get_required(model, operation_id, model.__name__)
    if not isinstance(operation, model):
        return operation
    if operation.status.name not in ("DRAFT", "WAITING") or not operation.items:
        return fail("A DRAFT or WAITING operation with items is required", 409)
    if model is Delivery:
        has_shortage = False
        for item in operation.items:
            stock = db().scalar(select(Stock).where(Stock.product_id == item.product_id, Stock.location_id == item.location_id))
            if not stock or stock.free_to_use < item.quantity:
                has_shortage = True
                break
        if has_shortage:
            operation.status = DeliveryStatus.WAITING
            commit()
            return jsonify(data(operation))
    operation.status = ReceiptStatus.READY if model is Receipt else DeliveryStatus.READY
    commit()
    return jsonify(data(operation))


@api_bp.post("/receipts/<uuid:receipt_id>/ready")
def ready_receipt(receipt_id: UUID):
    return mark_ready(Receipt, receipt_id)


@api_bp.post("/deliveries/<uuid:delivery_id>/ready")
def ready_delivery(delivery_id: UUID):
    return mark_ready(Delivery, delivery_id)


def validate_operation(model: type, operation_id: UUID, body: dict[str, Any]):
    required(body, "created_by")
    created_by = as_uuid(body["created_by"], "created_by")
    try:
        operation = validate_receipt(db(), operation_id, created_by) if model is Receipt else validate_delivery(db(), operation_id, created_by)
        commit()
    except ValueError as exc:
        db().rollback()
        return fail(str(exc), 409)
    return jsonify(data(operation))


@api_bp.post("/receipts/<uuid:receipt_id>/validate")
def validate_receipt_route(receipt_id: UUID):
    return validate_operation(Receipt, receipt_id, payload())


@api_bp.post("/deliveries/<uuid:delivery_id>/validate")
def validate_delivery_route(delivery_id: UUID):
    return validate_operation(Delivery, delivery_id, payload())


@api_bp.post("/transfers")
def create_transfer():
    body = payload()
    required(body, "reference", "from_location_id", "to_location_id", "responsible_id")
    from_location_id = as_uuid(body["from_location_id"], "from_location_id")
    to_location_id = as_uuid(body["to_location_id"], "to_location_id")
    responsible_id = as_uuid(body["responsible_id"], "responsible_id")
    if from_location_id == to_location_id:
        return fail("Source and destination locations must be different", 422)
    if not all((isinstance(get_required(Location, from_location_id, "Source location"), Location), isinstance(get_required(Location, to_location_id, "Destination location"), Location), isinstance(get_required(User, responsible_id, "User"), User))):
        return fail("Source, destination, or user not found", 404)
    transfer = StockTransfer(reference=body["reference"], from_location_id=from_location_id, to_location_id=to_location_id, responsible_id=responsible_id)
    db().add(transfer)
    commit()
    return jsonify(data(transfer)), 201


@api_bp.get("/transfers")
def list_transfers():
    query = select(StockTransfer).order_by(StockTransfer.id.desc())
    return jsonify(items=[data(item) for item in db().scalars(query).all()])


@api_bp.post("/transfers/<uuid:transfer_id>/items")
def add_transfer_item(transfer_id: UUID):
    body = payload()
    transfer = get_required(StockTransfer, transfer_id, "Transfer")
    if not isinstance(transfer, StockTransfer):
        return transfer
    if transfer.status != TransferStatus.DRAFT:
        return fail("Only DRAFT transfers can be edited", 409)
    required(body, "product_id", "quantity")
    product_id = as_uuid(body["product_id"], "product_id")
    if not isinstance(get_required(Product, product_id, "Product"), Product):
        return fail("Product not found", 404)
    item = TransferItem(transfer_id=transfer_id, product_id=product_id, quantity=decimal_value(body["quantity"], "quantity"))
    db().add(item)
    commit()
    return jsonify(data(item)), 201


@api_bp.post("/transfers/<uuid:transfer_id>/ready")
def ready_transfer(transfer_id: UUID):
    transfer = get_required(StockTransfer, transfer_id, "Transfer")
    if not isinstance(transfer, StockTransfer):
        return transfer
    if transfer.status != TransferStatus.DRAFT or not transfer.items:
        return fail("A DRAFT transfer with items is required", 409)
    transfer.status = TransferStatus.READY
    commit()
    return jsonify(data(transfer))


@api_bp.post("/transfers/<uuid:transfer_id>/validate")
def validate_transfer_route(transfer_id: UUID):
    body = payload()
    required(body, "created_by")
    try:
        transfer = validate_transfer(db(), transfer_id, as_uuid(body["created_by"], "created_by"))
        commit()
    except ValueError as exc:
        db().rollback()
        return fail(str(exc), 409)
    return jsonify(data(transfer))


@api_bp.post("/adjustments")
def create_adjustment():
    body = payload()
    required(body, "reference", "warehouse_id", "location_id", "responsible_id")
    warehouse_id, location_id, responsible_id = (as_uuid(body[key], key) for key in ("warehouse_id", "location_id", "responsible_id"))
    if not all((isinstance(get_required(Warehouse, warehouse_id, "Warehouse"), Warehouse), isinstance(get_required(Location, location_id, "Location"), Location), isinstance(get_required(User, responsible_id, "User"), User))):
        return fail("Warehouse, location, or user not found", 404)
    adjustment = StockAdjustment(reference=body["reference"], warehouse_id=warehouse_id, location_id=location_id, responsible_id=responsible_id, reason=body.get("reason"))
    db().add(adjustment)
    commit()
    return jsonify(data(adjustment)), 201


@api_bp.get("/adjustments")
def list_adjustments():
    query = select(StockAdjustment).order_by(StockAdjustment.id.desc())
    return jsonify(items=[data(item) for item in db().scalars(query).all()])


@api_bp.post("/adjustments/<uuid:adjustment_id>/items")
def add_adjustment_item(adjustment_id: UUID):
    body = payload()
    adjustment = get_required(StockAdjustment, adjustment_id, "Adjustment")
    if not isinstance(adjustment, StockAdjustment):
        return adjustment
    if adjustment.status != AdjustmentStatus.DRAFT:
        return fail("Only DRAFT adjustments can be edited", 409)
    required(body, "product_id", "new_quantity")
    product_id = as_uuid(body["product_id"], "product_id")
    if not isinstance(get_required(Product, product_id, "Product"), Product):
        return fail("Product not found", 404)
    stock = get_or_create_stock(db(), product_id, adjustment.location_id)
    new_quantity = decimal_value(body["new_quantity"], "new_quantity", allow_zero=True)
    item = StockAdjustmentItem(adjustment_id=adjustment_id, product_id=product_id, old_quantity=stock.on_hand_quantity, new_quantity=new_quantity, difference=new_quantity - stock.on_hand_quantity)
    db().add(item)
    commit()
    return jsonify(data(item)), 201


@api_bp.post("/adjustments/<uuid:adjustment_id>/validate")
def validate_adjustment_route(adjustment_id: UUID):
    body = payload()
    required(body, "created_by")
    try:
        adjustment = validate_adjustment(db(), adjustment_id, as_uuid(body["created_by"], "created_by"))
        commit()
    except ValueError as exc:
        db().rollback()
        return fail(str(exc), 409)
    return jsonify(data(adjustment))


@api_bp.get("/ledger")
def list_ledger():
    query = select(StockMove).order_by(StockMove.id.desc())
    if product_id := request.args.get("product_id", type=UUID):
        query = query.where(StockMove.product_id == product_id)
    if location_id := request.args.get("location_id", type=UUID):
        query = query.where((StockMove.from_location_id == location_id) | (StockMove.to_location_id == location_id))
    return jsonify(items=[data(item) for item in db().scalars(query).all()])


@api_bp.get("/dashboard/summary")
def dashboard_summary():
    available = Stock.on_hand_quantity - Stock.reserved_quantity
    return jsonify(
        total_products=db().scalar(select(func.count(func.distinct(Stock.product_id))).where(available > 0)) or 0,
        low_stock_items=db().scalar(select(func.count(func.distinct(Stock.product_id))).join(Product).where(available > 0, available <= Product.reorder_level)) or 0,
        out_of_stock_items=db().scalar(select(func.count(func.distinct(Stock.product_id))).where(available <= 0)) or 0,
        pending_receipts=db().scalar(select(func.count()).select_from(Receipt).where(Receipt.status.in_([ReceiptStatus.DRAFT, ReceiptStatus.READY]))) or 0,
        pending_deliveries=db().scalar(select(func.count()).select_from(Delivery).where(Delivery.status.in_([DeliveryStatus.DRAFT, DeliveryStatus.WAITING, DeliveryStatus.READY]))) or 0,
        scheduled_transfers=db().scalar(select(func.count()).select_from(StockTransfer).where(StockTransfer.status.in_([TransferStatus.DRAFT, TransferStatus.READY]))) or 0,
    )
