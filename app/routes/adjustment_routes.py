from flask import Blueprint, request, jsonify

adjustment_bp = Blueprint("adjustments", __name__)


@adjustment_bp.get("")
def get_adjustments():
    # TODO: filter by status, warehouse, location, date range
    return jsonify({"items": [], "total": 0}), 200


@adjustment_bp.post("")
def create_adjustment():
    data = request.get_json() or {}
    # TODO: create StockAdjustment in DRAFT
    return jsonify({"message": "Adjustment created", "data": data}), 201


@adjustment_bp.get("/<uuid:adjustment_id>")
def get_adjustment(adjustment_id):
    # TODO: return adjustment with items
    return jsonify({"id": str(adjustment_id)}), 200


@adjustment_bp.put("/<uuid:adjustment_id>")
def update_adjustment(adjustment_id):
    data = request.get_json() or {}
    # TODO: update adjustment
    return jsonify({"id": str(adjustment_id), "data": data}), 200


@adjustment_bp.delete("/<uuid:adjustment_id>")
def delete_adjustment(adjustment_id):
    # TODO: delete draft or cancel
    return jsonify({"message": "Adjustment deleted"}), 200


@adjustment_bp.post("/<uuid:adjustment_id>/items")
def add_adjustment_item(adjustment_id):
    data = request.get_json() or {}
    # TODO: read current stock and calculate old/count/difference
    return jsonify({"message": "Adjustment item added", "adjustment_id": str(adjustment_id), "data": data}), 201


@adjustment_bp.put("/<uuid:adjustment_id>/items/<uuid:item_id>")
def update_adjustment_item(adjustment_id, item_id):
    data = request.get_json() or {}
    # TODO: update counted quantity and difference
    return jsonify({"message": "Adjustment item updated", "item_id": str(item_id), "data": data}), 200


@adjustment_bp.delete("/<uuid:adjustment_id>/items/<uuid:item_id>")
def delete_adjustment_item(adjustment_id, item_id):
    # TODO: delete AdjustmentItem
    return jsonify({"message": "Adjustment item deleted"}), 200


@adjustment_bp.post("/<uuid:adjustment_id>/validate")
def validate_adjustment(adjustment_id):
    # TODO:
    # 1. apply counted_quantity to Stock
    # 2. create ADJUSTMENT ledger entry using difference
    # 3. mark DONE
    # 4. commit as one DB transaction
    return jsonify({"message": "Adjustment validation endpoint"}), 200


@adjustment_bp.post("/<uuid:adjustment_id>/cancel")
def cancel_adjustment(adjustment_id):
    # TODO: mark adjustment CANCELLED
    return jsonify({"message": "Adjustment cancelled"}), 200
