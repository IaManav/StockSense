from flask import Blueprint, request, jsonify

delivery_bp = Blueprint("deliveries", __name__)


@delivery_bp.get("")
def get_deliveries():
    # TODO: filter by status, warehouse_id, date range
    return jsonify({"items": [], "total": 0}), 200


@delivery_bp.post("")
def create_delivery():
    data = request.get_json() or {}
    # TODO: create delivery in DRAFT state
    return jsonify({"message": "Delivery created", "data": data}), 201


@delivery_bp.get("/<uuid:delivery_id>")
def get_delivery(delivery_id):
    # TODO: return delivery with items
    return jsonify({"id": str(delivery_id)}), 200


@delivery_bp.put("/<uuid:delivery_id>")
def update_delivery(delivery_id):
    data = request.get_json() or {}
    # TODO: allow edits only in appropriate status
    return jsonify({"id": str(delivery_id), "data": data}), 200


@delivery_bp.delete("/<uuid:delivery_id>")
def delete_delivery(delivery_id):
    # TODO: delete draft or use cancel
    return jsonify({"message": "Delivery deleted"}), 200


@delivery_bp.post("/<uuid:delivery_id>/items")
def add_delivery_item(delivery_id):
    data = request.get_json() or {}
    # TODO: add DeliveryItem
    return jsonify({"message": "Delivery item added", "delivery_id": str(delivery_id), "data": data}), 201


@delivery_bp.put("/<uuid:delivery_id>/items/<uuid:item_id>")
def update_delivery_item(delivery_id, item_id):
    data = request.get_json() or {}
    # TODO: update DeliveryItem
    return jsonify({"message": "Delivery item updated", "item_id": str(item_id), "data": data}), 200


@delivery_bp.delete("/<uuid:delivery_id>/items/<uuid:item_id>")
def delete_delivery_item(delivery_id, item_id):
    # TODO: delete DeliveryItem
    return jsonify({"message": "Delivery item deleted"}), 200


@delivery_bp.post("/<uuid:delivery_id>/ready")
def mark_delivery_ready(delivery_id):
    # TODO: DRAFT -> WAITING/READY according to your UI workflow
    return jsonify({"message": "Delivery marked ready"}), 200


@delivery_bp.post("/<uuid:delivery_id>/validate")
def validate_delivery(delivery_id):
    # TODO:
    # 1. verify status
    # 2. check free_to_use/on-hand stock
    # 3. decrement Stock
    # 4. create StockLedger OUT entries
    # 5. mark delivery DONE
    # 6. commit as one DB transaction
    return jsonify({"message": "Delivery validation endpoint"}), 200


@delivery_bp.post("/<uuid:delivery_id>/cancel")
def cancel_delivery(delivery_id):
    # TODO: mark delivery CANCELLED
    return jsonify({"message": "Delivery cancelled"}), 200
