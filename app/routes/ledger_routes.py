from flask import Blueprint, request, jsonify

ledger_bp = Blueprint("ledger", __name__)


@ledger_bp.get("")
def get_ledger():
    # TODO: filter by product_id, location_id, move_type,
    # source_type, from_date, to_date
    filters = {
        "product_id": request.args.get("product_id"),
        "location_id": request.args.get("location_id"),
        "move_type": request.args.get("move_type"),
        "source_type": request.args.get("source_type"),
        "from_date": request.args.get("from_date"),
        "to_date": request.args.get("to_date"),
    }
    return jsonify({"filters": filters, "items": []}), 200


@ledger_bp.get("/<uuid:ledger_id>")
def get_ledger_entry(ledger_id):
    # TODO: query ledger entry
    return jsonify({"id": str(ledger_id)}), 200
