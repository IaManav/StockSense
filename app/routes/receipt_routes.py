from flask import Blueprint, request, jsonify

receipt_bp = Blueprint("receipts", __name__)


@receipt_bp.get("")
def get_receipts():
    # TODO: filter by status, warehouse_id, date range
    return jsonify({"items": [], "total": 0}), 200


@receipt_bp.post("")
def create_receipt():
    data = request.get_json() or {}
    # TODO: create receipt in DRAFT state
    return jsonify({"message": "Receipt created", "data": data}), 201


@receipt_bp.get("/<uuid:receipt_id>")
def get_receipt(receipt_id):
    # TODO: return receipt with items
    return jsonify({"id": str(receipt_id)}), 200


@receipt_bp.put("/<uuid:receipt_id>")
def update_receipt(receipt_id):
    data = request.get_json() or {}
    # TODO: allow edits only in appropriate status
    return jsonify({"id": str(receipt_id), "data": data}), 200


@receipt_bp.delete("/<uuid:receipt_id>")
def delete_receipt(receipt_id):
    # TODO: delete draft or use cancel
    return jsonify({"message": "Receipt deleted"}), 200


@receipt_bp.post("/<uuid:receipt_id>/items")
def add_receipt_item(receipt_id):
    data = request.get_json() or {}
    # TODO: add ReceiptItem
    return jsonify({"message": "Receipt item added", "receipt_id": str(receipt_id), "data": data}), 201


@receipt_bp.put("/<uuid:receipt_id>/items/<uuid:item_id>")
def update_receipt_item(receipt_id, item_id):
    data = request.get_json() or {}
    # TODO: update ReceiptItem
    return jsonify({"message": "Receipt item updated", "item_id": str(item_id), "data": data}), 200


@receipt_bp.delete("/<uuid:receipt_id>/items/<uuid:item_id>")
def delete_receipt_item(receipt_id, item_id):
    # TODO: delete ReceiptItem
    return jsonify({"message": "Receipt item deleted"}), 200


@receipt_bp.post("/<uuid:receipt_id>/ready")
def mark_receipt_ready(receipt_id):
    # TODO: DRAFT -> READY
    return jsonify({"message": "Receipt marked READY"}), 200


@receipt_bp.post("/<uuid:receipt_id>/validate")
def validate_receipt(receipt_id):
    # TODO:
    # 1. verify status
    # 2. update Stock
    # 3. create StockLedger IN entries
    # 4. mark receipt DONE
    # 5. commit as one DB transaction
    return jsonify({"message": "Receipt validation endpoint"}), 200


@receipt_bp.post("/<uuid:receipt_id>/cancel")
def cancel_receipt(receipt_id):
    # TODO: mark receipt CANCELLED
    return jsonify({"message": "Receipt cancelled"}), 200
