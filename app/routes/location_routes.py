from flask import Blueprint, request, jsonify

location_bp = Blueprint("locations", __name__)


@location_bp.get("")
def get_locations():
    # TODO: support warehouse_id filter
    warehouse_id = request.args.get("warehouse_id")
    return jsonify({"items": [], "total": 0, "warehouse_id": warehouse_id}), 200


@location_bp.post("")
def create_location():
    data = request.get_json() or {}
    # TODO: validate warehouse_id and create location
    return jsonify({"message": "Location created", "data": data}), 201


@location_bp.get("/<uuid:location_id>")
def get_location(location_id):
    # TODO: query location
    return jsonify({"id": str(location_id)}), 200


@location_bp.put("/<uuid:location_id>")
def update_location(location_id):
    data = request.get_json() or {}
    # TODO: update location
    return jsonify({"id": str(location_id), "data": data}), 200


@location_bp.delete("/<uuid:location_id>")
def delete_location(location_id):
    # TODO: delete/deactivate location
    return jsonify({"message": "Location deleted"}), 200
