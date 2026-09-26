from flask import Blueprint, request, jsonify

category_bp = Blueprint("categories", __name__)


@category_bp.get("")
def get_categories():
    # TODO: query categories
    return jsonify({"items": [], "total": 0}), 200


@category_bp.post("")
def create_category():
    data = request.get_json() or {}
    # TODO: validate unique category name and create
    return jsonify({"message": "Category created", "data": data}), 201


@category_bp.get("/<uuid:category_id>")
def get_category(category_id):
    # TODO: query category
    return jsonify({"id": str(category_id)}), 200


@category_bp.put("/<uuid:category_id>")
def update_category(category_id):
    data = request.get_json() or {}
    # TODO: update category
    return jsonify({"id": str(category_id), "data": data}), 200


@category_bp.delete("/<uuid:category_id>")
def delete_category(category_id):
    # TODO: prevent deletion if products depend on category
    return jsonify({"message": "Category deleted"}), 200
