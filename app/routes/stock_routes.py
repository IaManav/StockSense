from flask import Blueprint, request, jsonify

stock_bp = Blueprint("stock", __name__)


@stock_bp.get("")
def get_stock():
    # TODO: filter by product_id, location_id, warehouse_id
    filters = {
        "product_id": request.args.get("product_id"),
        "location_id": request.args.get("location_id"),
        "warehouse_id": request.args.get("warehouse_id"),
    }
    return jsonify({"filters": filters, "items": []}), 200


@stock_bp.get("/<uuid:product_id>")
def get_product_stock(product_id):
    # TODO: return stock records for product
    return jsonify({"product_id": str(product_id), "items": []}), 200


@stock_bp.get("/location/<uuid:location_id>")
def get_location_stock(location_id):
    # TODO: return stock at location
    return jsonify({"location_id": str(location_id), "items": []}), 200


@stock_bp.get("/warehouse/<uuid:warehouse_id>")
def get_warehouse_stock(warehouse_id):
    # TODO: aggregate stock for warehouse
    return jsonify({"warehouse_id": str(warehouse_id), "items": []}), 200


@stock_bp.get("/low-stock")
def get_low_stock():
    # TODO: compare free/on-hand quantity against reorder_level
    return jsonify({"items": []}), 200


@stock_bp.get("/out-of-stock")
def get_out_of_stock():
    # TODO: find products with zero usable stock
    return jsonify({"items": []}), 200
