from flask import Blueprint, request, jsonify

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/summary")
def dashboard_summary():
    # TODO: calculate:
    # - total products in stock
    # - low stock items
    # - out of stock items
    # - pending receipts
    # - pending deliveries
    # - scheduled internal transfers
    return jsonify({
        "total_products": 0,
        "low_stock_items": 0,
        "out_of_stock_items": 0,
        "pending_receipts": 0,
        "pending_deliveries": 0,
        "scheduled_transfers": 0
    }), 200


@dashboard_bp.get("/stock")
def dashboard_stock():
    # TODO: stock summary by warehouse/location/category
    filters = {
        "warehouse_id": request.args.get("warehouse_id"),
        "location_id": request.args.get("location_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"filters": filters, "items": []}), 200


@dashboard_bp.get("/operations")
def dashboard_operations():
    # TODO: support:
    # document_type = receipts/deliveries/transfers/adjustments
    # status = DRAFT/WAITING/READY/DONE/CANCELLED
    # warehouse_id/location_id/category_id
    filters = {
        "document_type": request.args.get("document_type"),
        "status": request.args.get("status"),
        "warehouse_id": request.args.get("warehouse_id"),
        "location_id": request.args.get("location_id"),
        "category_id": request.args.get("category_id"),
    }
    return jsonify({"filters": filters, "items": []}), 200
