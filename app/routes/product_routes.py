from flask import Blueprint, request, jsonify

product_bp = Blueprint("products", __name__)


@product_bp.get("")
def get_products():
    # TODO: support search/category_id/is_active filters and pagination
    return jsonify({"items": [], "total": 0}), 200


@product_bp.post("")
def create_product():
    data = request.get_json() or {}
    # TODO: validate SKU/category and create product
    # Optional initial stock should be handled transactionally.
    return jsonify({"message": "Product created", "data": data}), 201


@product_bp.get("/search")
def search_products():
    query = request.args.get("q", "").strip()
    # TODO: search by SKU/name
    return jsonify({"query": query, "items": []}), 200


@product_bp.get("/<uuid:product_id>")
def get_product(product_id):
    # TODO: query product
    return jsonify({"id": str(product_id)}), 200


@product_bp.put("/<uuid:product_id>")
def update_product(product_id):
    data = request.get_json() or {}
    # TODO: update product
    return jsonify({"id": str(product_id), "data": data}), 200


@product_bp.delete("/<uuid:product_id>")
def delete_product(product_id):
    # TODO: preferably deactivate product using is_active
    return jsonify({"message": "Product deactivated"}), 200


@product_bp.get("/<uuid:product_id>/stock")
def get_product_stock(product_id):
    # TODO: return stock by location
    return jsonify({"product_id": str(product_id), "items": []}), 200


@product_bp.get("/<uuid:product_id>/locations")
def get_product_locations(product_id):
    # TODO: return locations containing this product
    return jsonify({"product_id": str(product_id), "items": []}), 200
