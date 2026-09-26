from flask import Blueprint, request, jsonify

user_bp = Blueprint("users", __name__)


@user_bp.get("/me")
def get_profile():
    # TODO: get authenticated user
    return jsonify({"message": "Profile endpoint"}), 200


@user_bp.put("/me")
def update_profile():
    data = request.get_json() or {}
    # TODO: update authenticated user
    return jsonify({"message": "Profile updated", "data": data}), 200


@user_bp.put("/me/password")
def change_password():
    data = request.get_json() or {}
    # TODO: change authenticated user's password
    return jsonify({"message": "Password updated"}), 200
