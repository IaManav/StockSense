from flask import Blueprint, request, jsonify

transfer_bp = Blueprint("transfers", __name__)


@transfer_bp.get("")
def get_transfers():
    # TODO: filter by status/from_location/to_location/date
    return jsonify({"items": [], "total": 0}), 200


@transfer_bp.post("")
def create_transfer():
    data = request.get_json() or {}
    # TODO: create StockTransfer in DRAFT
    return jsonify({"message": "Transfer created", "data": data}), 201


@transfer_bp.get("/<uuid:transfer_id>")
def get_transfer(transfer_id):
    # TODO: return transfer with items
    return jsonify({"id": str(transfer_id)}), 200


@transfer_bp.put("/<uuid:transfer_id>")
def update_transfer(transfer_id):
    data = request.get_json() or {}
    # TODO: update transfer
    return jsonify({"id": str(transfer_id), "data": data}), 200


@transfer_bp.delete("/<uuid:transfer_id>")
def delete_transfer(transfer_id):
    # TODO: delete draft or cancel
    return jsonify({"message": "Transfer deleted"}), 200


@transfer_bp.post("/<uuid:transfer_id>/items")
def add_transfer_item(transfer_id):
    data = request.get_json() or {}
    # TODO: add TransferItem
    return jsonify({"message": "Transfer item added", "transfer_id": str(transfer_id), "data": data}), 201


@transfer_bp.put("/<uuid:transfer_id>/items/<uuid:item_id>")
def update_transfer_item(transfer_id, item_id):
    data = request.get_json() or {}
    # TODO: update TransferItem
    return jsonify({"message": "Transfer item updated", "item_id": str(item_id), "data": data}), 200


@transfer_bp.delete("/<uuid:transfer_id>/items/<uuid:item_id>")
def delete_transfer_item(transfer_id, item_id):
    # TODO: delete TransferItem
    return jsonify({"message": "Transfer item deleted"}), 200


@transfer_bp.post("/<uuid:transfer_id>/ready")
def mark_transfer_ready(transfer_id):
    # TODO: DRAFT -> READY
    return jsonify({"message": "Transfer marked READY"}), 200


@transfer_bp.post("/<uuid:transfer_id>/validate")
def validate_transfer(transfer_id):
    # TODO:
    # 1. check source stock
    # 2. source quantity -= quantity
    # 3. destination quantity += quantity
    # 4. create TRANSFER ledger entry
    # 5. mark DONE
    # 6. commit as one DB transaction
    return jsonify({"message": "Transfer validation endpoint"}), 200


@transfer_bp.post("/<uuid:transfer_id>/cancel")
def cancel_transfer(transfer_id):
    # TODO: mark transfer CANCELLED
    return jsonify({"message": "Transfer cancelled"}), 200
