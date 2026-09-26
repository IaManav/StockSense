from flask import Blueprint, request, jsonify

warehouse_bp = Blueprint("warehouses", __name__)


@warehouse_bp.get("")
def get_warehouses():
    # TODO: query warehouses
    return jsonify({"items": [], "total": 0}), 200


@warehouse_bp.post("")
def create_warehouse():
    data = request.get_json() or {}
    # TODO: validate and create warehouse
    return jsonify({"message": "Warehouse created", "data": data}), 201


@warehouse_bp.get("/<uuid:warehouse_id>")
def get_warehouse(warehouse_id):
    # TODO: query warehouse
    return jsonify({"id": str(warehouse_id)}), 200


@warehouse_bp.put("/<uuid:warehouse_id>")
def update_warehouse(warehouse_id):
    data = request.get_json() or {}
    # TODO: update warehouse
    return jsonify({"id": str(warehouse_id), "data": data}), 200


@warehouse_bp.delete("/<uuid:warehouse_id>")
def delete_warehouse(warehouse_id):
    # TODO: delete/deactivate warehouse
    return jsonify({"message": "Warehouse deleted"}), 200


@warehouse_bp.get("/<uuid:warehouse_id>/locations")
def get_warehouse_locations(warehouse_id):
    # TODO: query locations belonging to warehouse
    return jsonify({"warehouse_id": str(warehouse_id), "items": []}), 200
