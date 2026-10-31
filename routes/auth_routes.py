from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from database import get_db
from utils.auth_helpers import hash_password, check_password, serialize_doc
from utils.validators import validate_registration, validate_login

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_registration(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    db = get_db()
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"success": False, "message": "An account with this email already exists."}), 409

    hashed_pw = hash_password(password)
    new_user = {
        "name": name,
        "email": email,
        "password_hash": hashed_pw,
        "created_at": datetime.utcnow(),
        "currency": data.get("currency", "USD")
    }

    insert_result = db.users.insert_one(new_user)
    user_id = str(insert_result.inserted_id)

    access_token = create_access_token(identity=user_id)

    return jsonify({
        "success": True,
        "message": "Registration successful. Welcome to Finora!",
        "token": access_token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
            "currency": new_user["currency"]
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    is_valid, errors = validate_login(data)
    if not is_valid:
        return jsonify({"success": False, "message": "Validation failed", "errors": errors}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not check_password(password, user.get("password_hash", "")):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    user_id = str(user["_id"])
    access_token = create_access_token(identity=user_id)

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": access_token,
        "user": {
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "currency": user.get("currency", "USD")
        }
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(optional=True)
def logout():
    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    }), 200

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    db = get_db()
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found."}), 404

        return jsonify({
            "success": True,
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "currency": user.get("currency", "USD"),
                "created_at": user.get("created_at").isoformat() if isinstance(user.get("created_at"), datetime) else user.get("created_at")
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Error retrieving profile", "error": str(e)}), 500
