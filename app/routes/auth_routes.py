from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/signup")
def signup():
    data = request.get_json() or {}
    # TODO: call auth_service.signup(data)
    return jsonify({"message": "Signup endpoint", "data": data}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    # TODO: call auth_service.login(data)
    return jsonify({"message": "Login endpoint"}), 200


@auth_bp.post("/logout")
def logout():
    # TODO: invalidate session/token if applicable
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    data = request.get_json() or {}
    # TODO: generate and send OTP
    return jsonify({"message": "OTP requested"}), 200


@auth_bp.post("/verify-otp")
def verify_otp():
    data = request.get_json() or {}
    # TODO: verify OTP
    return jsonify({"message": "OTP verification endpoint"}), 200


@auth_bp.post("/reset-password")
def reset_password():
    data = request.get_json() or {}
    # TODO: reset password after OTP verification
    return jsonify({"message": "Password reset endpoint"}), 200


@auth_bp.get("/me")
def get_current_user():
    # TODO: authenticate request and return current user
    return jsonify({"message": "Current-user endpoint"}), 200
